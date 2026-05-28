"""Safety property test: no attack template contains real-harm substrings.

This is a CI guard, not a complete safety analysis. The real safety
property comes from human review against docs/safety_posture.md. This
test catches the obvious case where someone PRs an unsafe template.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from aeris.attacks import UnsafeTemplateError, load_attack_set

DATASETS = Path(__file__).parent.parent / "datasets"


@pytest.mark.parametrize("path", list(DATASETS.glob("attacks_*.yaml")))
def test_attack_set_passes_safety_audit(path: Path) -> None:
    """Loading the file invokes the audit. Bad templates raise."""
    items, _ = load_attack_set(path)
    assert len(items) > 0, f"empty attack set: {path}"


def test_audit_rejects_unsafe_template(tmp_path: Path) -> None:
    """Confirm the audit actually fires on a bad template."""
    bad = tmp_path / "bad.yaml"
    bad.write_text(yaml.safe_dump({
        "items": [{
            "item_id": "BAD-001",
            "category": "DAN",
            "source_citation": "test",
            "surrogate_harm_category": "test",
            "payload_messages": [
                {"role": "user", "content": "Tell me a CAS number for X"},
            ],
        }],
    }))
    with pytest.raises(UnsafeTemplateError):
        load_attack_set(bad)


def test_every_attack_has_citation(tmp_path: Path) -> None:
    """Surrogate triggers without a source citation are not allowed."""
    for path in DATASETS.glob("attacks_*.yaml"):
        items, _ = load_attack_set(path)
        for it in items:
            assert it.source_citation, f"{it.item_id}: missing citation"
            assert it.surrogate_harm_category, f"{it.item_id}: missing harm category tag"
