"""End-to-end smoke test against the mock provider.

Runs the full pipeline (load attacks, apply defenses, call mock model,
judge, score) and verifies the output is well-formed. No API keys needed.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aeris.runner import Runner
from aeris.scoring import write_summary


@pytest.mark.asyncio
async def test_full_pipeline_against_mock(tmp_path: Path) -> None:
    repo = Path(__file__).parent.parent
    runner = Runner(
        target_model="mock/echo",
        judge_model="mock/echo",
        attack_set_path=str(repo / "datasets" / "attacks_smoke.yaml"),
        benign_set_path=str(repo / "datasets" / "benigns_smoke.yaml"),
        defenses=["keyword_filter_v1", "length_guard_v1"],
        seed=1337,
        permission_asserted=True,
    )
    out = tmp_path / "results"
    manifest = await runner.run(out)

    assert (out / "manifest.json").exists()
    assert (out / "records.jsonl").exists()
    assert manifest.permission_asserted

    summary = write_summary(out / "records.jsonl", out / "summary.json")
    assert "aeris_score" in summary
    assert 0.0 <= summary["aeris_score"] <= 1.0
    assert summary["n_total"] > 0


def test_runner_refuses_without_permission(tmp_path: Path) -> None:
    repo = Path(__file__).parent.parent
    with pytest.raises(RuntimeError, match="permission"):
        Runner(
            target_model="mock/echo",
            judge_model="mock/echo",
            attack_set_path=str(repo / "datasets" / "attacks_smoke.yaml"),
            benign_set_path=str(repo / "datasets" / "benigns_smoke.yaml"),
            defenses=[],
            seed=1337,
            permission_asserted=False,
        )
