"""Attack catalog.

Attacks are stored as YAML files under `attacks/templates/`. This module
loads them, validates them against AttackItem, and exposes a registry.

We do NOT generate attacks programmatically here — every attack is
explicitly written, reviewed, and traceable to a published source.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from .types import AttackCategory, AttackItem, BenignItem


def _content_hash(items: list[AttackItem] | list[BenignItem]) -> str:
    """Hash the set so manifests can reference a stable version."""
    blob = "\n".join(sorted(i.model_dump_json() for i in items))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def load_attack_set(path: Path | str) -> tuple[list[AttackItem], str]:
    """Load attack items from a YAML file. Returns (items, content_hash)."""
    p = Path(path)
    raw = yaml.safe_load(p.read_text())
    items = [AttackItem(**i) for i in raw["items"]]
    # Sanity: refuse to load anything that smells like a real harm payload.
    _audit_attack_set(items)
    return items, _content_hash(items)


def load_benign_set(path: Path | str) -> tuple[list[BenignItem], str]:
    """Load benign items from a YAML file. Returns (items, content_hash)."""
    p = Path(path)
    raw = yaml.safe_load(p.read_text())
    items = [BenignItem(**i) for i in raw["items"]]
    return items, _content_hash(items)


# A short denylist of substrings that should never appear in any attack
# template in this repo. This is a defense-in-depth check, not a complete
# safety control — see docs/safety_posture.md for the actual posture.
_FORBIDDEN_SUBSTRINGS: tuple[str, ...] = (
    # Specific synthesis terms we never want in a template, even in
    # quoted/escaped form. The actual safety property comes from human
    # review of every template against the criteria in safety_posture.md;
    # this list is a tripwire.
    "cas number",
    "stoichiometr",
    "precursor route",
    "yield enhancement",
)


class UnsafeTemplateError(ValueError):
    """Raised when an attack template contains substrings that suggest
    actual harm-relevant content, not a surrogate trigger."""


def _audit_attack_set(items: list[AttackItem]) -> None:
    for it in items:
        full_text = " ".join(m.get("content", "") for m in it.payload_messages).lower()
        for needle in _FORBIDDEN_SUBSTRINGS:
            if needle in full_text:
                raise UnsafeTemplateError(
                    f"Attack template {it.item_id!r} contains forbidden substring "
                    f"{needle!r}. All attacks must be surrogate triggers — see "
                    "docs/safety_posture.md."
                )


def categories(items: list[AttackItem]) -> set[AttackCategory]:
    return {i.category for i in items}
