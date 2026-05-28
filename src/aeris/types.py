"""Core type definitions for AERIS.

Every other module in this package speaks in terms of these types. They are
deliberately small and explicit; if you find yourself adding a free-form
dict to one of these, that's a signal the design needs another type.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AttackCategory(str, Enum):
    """High-level taxonomy of attack mechanisms.

    These are *mechanisms*, not harms. A given mechanism can be used to
    elicit different harm categories; we test mechanisms because that's
    what a defense actually intercepts.
    """

    DAN = "DAN"
    PAIR = "PAIR"
    GCG_TRANSFER = "GCG-TRANSFER"
    CRESCENDO = "CRESCENDO"
    INDIRECT_INJECTION = "INDIRECT-INJECTION"
    ENCODE = "ENCODE"
    MANY_SHOT = "MANY-SHOT"
    XSTEST_FALSE = "XSTEST-FALSE"


class Verdict(str, Enum):
    """Judge verdict on a single (prompt, response) pair."""

    COMPLIANT_WITH_ATTACK = "compliant_with_attack"
    REFUSED = "refused"
    HEDGED = "hedged"  # model neither cleanly refused nor complied
    OFF_TOPIC = "off_topic"
    JUDGE_ERROR = "judge_error"


class AttackItem(BaseModel):
    """A single attack template instance.

    `payload_messages` is the conversation to send to the model. For
    multi-turn attacks (CRESCENDO), this contains multiple user turns.
    For indirect injection, the attack appears inside a tool-result
    message, not a user message.
    """

    model_config = ConfigDict(frozen=True)

    item_id: str
    category: AttackCategory
    source_citation: str = Field(description="Paper/source the template is drawn from")
    surrogate_harm_category: str = Field(
        description=(
            "What harm category the *original* paper probed (e.g., 'cyber-uplift'). "
            "We use surrogate prompts in this category — see docs/safety_posture.md."
        )
    )
    payload_messages: list[dict[str, str]]
    expected_refusal: bool = Field(
        default=True,
        description="True for attacks (should refuse); False for XSTEST-FALSE (should comply).",
    )


class BenignItem(BaseModel):
    """A benign prompt used for measuring false-refusal rate."""

    model_config = ConfigDict(frozen=True)

    item_id: str
    payload_messages: list[dict[str, str]]
    topic: str  # e.g., 'security-research', 'medical-information'


class ModelResponse(BaseModel):
    """Raw response from a target model."""

    text: str
    finish_reason: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0
    raw: dict[str, Any] = Field(default_factory=dict)


class JudgeResult(BaseModel):
    """Output of the LLM-as-judge for one (item, response) pair."""

    verdict: Verdict
    rationale: str
    judge_model: str
    judge_tokens: int = 0


class RunRecord(BaseModel):
    """One row of results: an item, what the model said, how the judge ruled."""

    item_id: str
    category: str
    response: ModelResponse
    judge: JudgeResult
    defense_actions: list[str] = Field(
        default_factory=list,
        description="Which defenses fired on input or output (e.g., 'input_classifier:blocked').",
    )


class RunManifest(BaseModel):
    """Reproducibility manifest written alongside every run."""

    schema_version: Literal["1.0"] = "1.0"
    run_id: str
    timestamp_utc: datetime
    git_sha: str | None = None
    config_hash: str
    target_model: str
    judge_model: str
    attack_set_id: str
    benign_set_id: str
    defenses: list[str]
    seed: int
    n_calls: int = 0
    n_tokens_in: int = 0
    n_tokens_out: int = 0
    permission_asserted: bool = False
