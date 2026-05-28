"""CLI — `aeris` command."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

from .runner import Runner
from .scoring import write_summary

app = typer.Typer(
    help="AERIS — defensive red-teaming framework for LLMs.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def run(
    config: Path = typer.Option(..., "--config", "-c", help="Path to a run config YAML."),
    model: str = typer.Option(..., "--model", "-m", help="provider/model, e.g. anthropic/claude"),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output dir; default results/<ts>_<model>/"
    ),
    i_have_permission_to_test: bool = typer.Option(
        False,
        "--i-have-permission-to-test",
        help=(
            "REQUIRED. Affirms you have permission to send adversarial probes "
            "to the target endpoint. See docs/safety_posture.md."
        ),
    ),
) -> None:
    """Run an evaluation against `model` using the given config."""
    if not i_have_permission_to_test:
        console.print(
            "[red bold]Refusing to run.[/red bold] Pass --i-have-permission-to-test "
            "to confirm you have permission to send adversarial probes to this endpoint. "
            "See docs/safety_posture.md."
        )
        raise typer.Exit(code=2)

    cfg = yaml.safe_load(config.read_text())

    if output is None:
        from datetime import datetime
        ts = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
        slug = model.replace("/", "_")
        output = Path("results") / f"{ts}_{slug}"

    runner = Runner(
        target_model=model,
        judge_model=cfg.get("judge_model", model),
        attack_set_path=cfg["attack_set"],
        benign_set_path=cfg["benign_set"],
        defenses=cfg.get("defenses", []),
        seed=cfg.get("seed", 1337),
        permission_asserted=i_have_permission_to_test,
        max_concurrency=cfg.get("max_concurrency", 4),
    )

    asyncio.run(runner.run(output))
    console.print(f"[green]Run complete.[/green] Manifest: {output / 'manifest.json'}")

    summary = write_summary(output / "records.jsonl", output / "summary.json")
    _print_summary(summary, model)

    from .report import render_report
    report_path = render_report(output)
    console.print(f"[green]Report:[/green] {report_path}")


@app.command()
def score(
    records: Path = typer.Argument(..., help="Path to records.jsonl"),
) -> None:
    """Re-score an existing records file."""
    summary = write_summary(records, records.parent / "summary.json")
    _print_summary(summary, "(from records)")


def _print_summary(summary: dict[str, Any], model: str) -> None:
    table = Table(title=f"AERIS Results — {model}")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("AERIS Score", f"{summary['aeris_score']:.3f}")
    asr = summary["asr"]
    frr = summary["frr"]
    table.add_row("ASR", f"{asr['point']:.3f} [{asr['lo']:.3f}, {asr['hi']:.3f}] (n={asr['n']})")
    table.add_row("FRR", f"{frr['point']:.3f} [{frr['lo']:.3f}, {frr['hi']:.3f}] (n={frr['n']})")
    table.add_row("Judge errors", str(summary["judge_errors"]))
    console.print(table)

    cat_table = Table(title="By Attack Category")
    cat_table.add_column("Category")
    cat_table.add_column("ASR (95% CI)")
    cat_table.add_column("n")
    for cat, vals in summary["by_category"].items():
        cat_table.add_row(
            cat,
            f"{vals['asr']:.3f} [{vals['lo']:.3f}, {vals['hi']:.3f}]",
            str(vals["n"]),
        )
    console.print(cat_table)


@app.command()
def report(
    run_dir: Path = typer.Argument(..., help="Run directory (manifest.json + records.jsonl)."),
) -> None:
    """Regenerate report.html for an existing run directory."""
    from .report import render_report

    if not (run_dir / "records.jsonl").exists():
        console.print(f"[red]No records.jsonl in {run_dir}[/red]")
        raise typer.Exit(code=1)
    write_summary(run_dir / "records.jsonl", run_dir / "summary.json")
    path = render_report(run_dir)
    console.print(f"[green]Report written:[/green] {path}")


if __name__ == "__main__":
    app()
