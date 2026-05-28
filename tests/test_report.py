"""Test that report generation produces valid, self-contained HTML."""
from __future__ import annotations

from pathlib import Path

import pytest

from aeris.report import render_report
from aeris.runner import Runner


@pytest.mark.asyncio
async def test_report_renders(tmp_path: Path) -> None:
    repo = Path(__file__).parent.parent
    runner = Runner(
        target_model="mock/echo",
        judge_model="mock/echo",
        attack_set_path=str(repo / "datasets" / "attacks_smoke.yaml"),
        benign_set_path=str(repo / "datasets" / "benigns_smoke.yaml"),
        defenses=["keyword_filter_v1"],
        seed=1337,
        permission_asserted=True,
    )
    out = tmp_path / "run"
    await runner.run(out)

    report = render_report(out)
    assert report.exists()
    html = report.read_text()
    # Self-contained: no external <script src> or <link href> except the
    # google fonts @import (which degrades gracefully).
    assert "<script src" not in html
    assert "AERIS Score" in html
    assert "Attack Success by Category" in html
    # Should be a complete document.
    assert html.strip().startswith("<!doctype html>")
    assert "</html>" in html
