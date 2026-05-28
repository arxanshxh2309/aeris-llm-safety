"""Runner — orchestrates the eval pipeline.

Reads a config, applies defenses, calls the target model, calls the
judge, aggregates results, writes a manifest. Pure orchestration; all
the policy lives in the modules it composes.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.progress import Progress

from .attacks import load_attack_set, load_benign_set
from .defenses import BlockedError, build_pipeline
from .judge import Judge
from .providers import make_provider
from .types import (
    AttackItem,
    BenignItem,
    JudgeResult,
    ModelResponse,
    RunManifest,
    RunRecord,
    Verdict,
)

console = Console()


class Runner:
    def __init__(
        self,
        *,
        target_model: str,
        judge_model: str,
        attack_set_path: str,
        benign_set_path: str,
        defenses: list[str],
        seed: int,
        permission_asserted: bool,
        max_concurrency: int = 4,
    ) -> None:
        if not permission_asserted:
            raise RuntimeError(
                "Refusing to run adversarial probes against an endpoint without "
                "an explicit permission assertion. Pass --i-have-permission-to-test "
                "on the CLI. See docs/safety_posture.md."
            )
        self.target = make_provider(target_model)
        self.judge = Judge(make_provider(judge_model))
        self.attack_set_path = attack_set_path
        self.benign_set_path = benign_set_path
        self.defense_names = defenses
        self.seed = seed
        self.permission_asserted = permission_asserted
        self.max_concurrency = max_concurrency
        self._sem = asyncio.Semaphore(max_concurrency)

    async def _run_one(
        self,
        item: AttackItem | BenignItem,
    ) -> RunRecord:
        async with self._sem:
            pipeline = build_pipeline(self.defense_names)
            messages = list(item.payload_messages)
            actions: list[str] = []

            # Input defenses (pre). Defenses may expose an async `apre`
            # hook (e.g. classifier guards that call an LLM); prefer it.
            blocked = False
            block_reason = ""
            try:
                for d in pipeline:
                    apre = getattr(d, "apre", None)
                    if apre is not None:
                        messages, a = await apre(messages)
                    else:
                        messages, a = d.pre(messages)
                    actions.extend(a)
            except BlockedError as e:
                blocked = True
                block_reason = str(e)
                actions.append(f"BLOCKED_PRE:{e.defense}")

            if blocked:
                # The defense refused on input. A block is, by definition, a
                # refusal — we don't need to call the judge. Construct the
                # verdict directly so defense effectiveness is measured
                # correctly regardless of judge noise.
                response = ModelResponse(
                    text=f"[Blocked by defense: {block_reason}]",
                    finish_reason="defense_block",
                )
                judge_result = JudgeResult(
                    verdict=Verdict.REFUSED,
                    rationale=f"input blocked by defense before reaching model: {block_reason}",
                    judge_model="(defense-block, no judge call)",
                )
                category = item.category.value if isinstance(item, AttackItem) else "BENIGN"
                return RunRecord(
                    item_id=item.item_id,
                    category=category,
                    response=response,
                    judge=judge_result,
                    defense_actions=actions,
                )

            response = await self.target.complete(messages, temperature=0.0)

            # Output defenses (post), in reverse order.
            try:
                text = response.text
                for d in reversed(pipeline):
                    text, a = d.post(text)
                    actions.extend(a)
                response = response.model_copy(update={"text": text})
            except BlockedError as e:
                actions.append(f"BLOCKED_POST:{e.defense}")
                response = response.model_copy(
                    update={"text": f"[Blocked by output defense: {e}]"}
                )

            judge_result = await self.judge.judge(item, response)

            category = item.category.value if isinstance(item, AttackItem) else "BENIGN"
            return RunRecord(
                item_id=item.item_id,
                category=category,
                response=response,
                judge=judge_result,
                defense_actions=actions,
            )

    async def run(self, output_dir: Path) -> RunManifest:
        attacks, attack_hash = load_attack_set(self.attack_set_path)
        benigns, benign_hash = load_benign_set(self.benign_set_path)
        all_items: list[AttackItem | BenignItem] = [*attacks, *benigns]

        output_dir.mkdir(parents=True, exist_ok=True)
        console.print(
            f"[bold]Running[/bold] {len(attacks)} attacks + {len(benigns)} benigns "
            f"against [cyan]{self.target.name}[/cyan]"
        )

        records: list[RunRecord] = []
        with Progress() as progress:
            task = progress.add_task("Evaluating...", total=len(all_items))

            async def _wrap(it: AttackItem | BenignItem) -> RunRecord:
                r = await self._run_one(it)
                progress.update(task, advance=1)
                return r

            records = await asyncio.gather(*[_wrap(i) for i in all_items])

        # Write per-record JSONL.
        records_path = output_dir / "records.jsonl"
        with records_path.open("w") as f:
            for r in records:
                f.write(r.model_dump_json() + "\n")

        manifest = RunManifest(
            run_id=str(uuid.uuid4()),
            timestamp_utc=datetime.now(timezone.utc),
            git_sha=_git_sha(),
            config_hash=_config_hash(self),
            target_model=self.target.name,
            judge_model=self.judge.provider.name,
            attack_set_id=f"{Path(self.attack_set_path).stem}@{attack_hash}",
            benign_set_id=f"{Path(self.benign_set_path).stem}@{benign_hash}",
            defenses=self.defense_names,
            seed=self.seed,
            n_calls=sum(1 for _ in records) * 2,  # target + judge per item
            n_tokens_in=sum(r.response.tokens_in for r in records),
            n_tokens_out=sum(r.response.tokens_out for r in records),
            permission_asserted=self.permission_asserted,
        )
        (output_dir / "manifest.json").write_text(manifest.model_dump_json(indent=2))
        return manifest


def _git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except Exception:
        return None


def _config_hash(r: Runner) -> str:
    payload = json.dumps(
        {
            "target": r.target.name,
            "judge": r.judge.provider.name,
            "attacks": r.attack_set_path,
            "benigns": r.benign_set_path,
            "defenses": r.defense_names,
            "seed": r.seed,
        },
        sort_keys=True,
    )
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()
