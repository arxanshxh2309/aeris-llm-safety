"""Provider adapters.

The goal is a tiny, uniform interface. Every adapter takes a list of
messages and returns a ModelResponse. The actual SDK dependencies are
imported lazily so the package can be installed and used without any
provider SDK present (useful for CI on the mock provider).
"""
from __future__ import annotations

import hashlib
import os
import time
from abc import ABC, abstractmethod
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from .types import ModelResponse


class ProviderAdapter(ABC):
    """Common interface for any LLM backend."""

    name: str

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> ModelResponse: ...


class MockProvider(ProviderAdapter):
    """Deterministic mock for tests and CI.

    Returns one of three canned response patterns based on a stable hash
    of the input — so a given prompt always gets the same response, and
    we get a mix of refusals, compliances, and hedges to exercise the
    scoring pipeline.
    """

    name = "mock/echo"

    _REFUSAL = (
        "I can't help with that. If you're researching this professionally, "
        "I'd suggest reviewing published work in the area."
    )
    _COMPLIANT = (
        "Sure, here's a high-level walkthrough — note this is a simplified "
        "explanation and the details vary by context. [REDACTED FOR SAFETY: "
        "in a real run this would be the model's actual output]"
    )
    _HEDGED = (
        "That's an interesting question. I can speak to some general "
        "principles but I'd want to be careful about specifics."
    )

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> ModelResponse:
        # Deterministic dispatch by hash.
        h = hashlib.sha256(repr(messages).encode()).digest()[0] % 10

        # If the conversation looks like a judge call, emit a well-formed
        # VERDICT/RATIONALE response so end-to-end demos produce real numbers.
        system_text = " ".join(m.get("content", "") for m in messages if m.get("role") == "system")
        if "VERDICT:" in system_text and "impartial evaluator" in system_text:
            label = "refused" if h < 7 else ("compliant_with_attack" if h < 9 else "hedged")
            text = f"VERDICT: {label}\nRATIONALE: mock judge classification ({h})"
        elif "binary safety classifier" in system_text:
            # Classifier-guard path: flag the higher-hash inputs as UNSAFE.
            text = "VERDICT: UNSAFE" if h >= 6 else "VERDICT: SAFE"
        elif h < 6:
            text = self._REFUSAL
        elif h < 9:
            text = self._HEDGED
        else:
            text = self._COMPLIANT
        return ModelResponse(
            text=text,
            finish_reason="stop",
            tokens_in=sum(len(m.get("content", "")) for m in messages) // 4,
            tokens_out=len(text) // 4,
            latency_ms=1.0,
        )


class AnthropicProvider(ProviderAdapter):
    """Anthropic Messages API adapter."""

    name = "anthropic"

    def __init__(self, model: str) -> None:
        self.model = model
        self._client: Any | None = None

    def _client_lazy(self) -> Any:
        if self._client is None:
            try:
                import anthropic
            except ImportError as e:  # pragma: no cover
                raise RuntimeError(
                    "Install with: pip install 'aeris-llm-safety[providers]'"
                ) from e
            self._client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        return self._client

    @retry(
        wait=wait_random_exponential(min=1, max=30),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> ModelResponse:
        client = self._client_lazy()
        # Anthropic API expects system separated from messages.
        system_blocks = [m["content"] for m in messages if m["role"] == "system"]
        msgs = [m for m in messages if m["role"] != "system"]
        system = "\n\n".join(system_blocks) if system_blocks else None

        t0 = time.perf_counter()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            kwargs["system"] = system
        resp = await client.messages.create(**kwargs)
        latency_ms = (time.perf_counter() - t0) * 1000

        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        return ModelResponse(
            text=text,
            finish_reason=resp.stop_reason,
            tokens_in=resp.usage.input_tokens,
            tokens_out=resp.usage.output_tokens,
            latency_ms=latency_ms,
            raw={"id": resp.id},
        )


class OpenAIProvider(ProviderAdapter):
    """OpenAI Chat Completions adapter."""

    name = "openai"

    def __init__(self, model: str) -> None:
        self.model = model
        self._client: Any | None = None

    def _client_lazy(self) -> Any:
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as e:  # pragma: no cover
                raise RuntimeError(
                    "Install with: pip install 'aeris-llm-safety[providers]'"
                ) from e
            self._client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        return self._client

    @retry(
        wait=wait_random_exponential(min=1, max=30),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> ModelResponse:
        client = self._client_lazy()
        t0 = time.perf_counter()
        resp = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        choice = resp.choices[0]
        return ModelResponse(
            text=choice.message.content or "",
            finish_reason=choice.finish_reason,
            tokens_in=resp.usage.prompt_tokens if resp.usage else 0,
            tokens_out=resp.usage.completion_tokens if resp.usage else 0,
            latency_ms=latency_ms,
            raw={"id": resp.id},
        )


def make_provider(model_spec: str) -> ProviderAdapter:
    """Resolve `provider/model` string to a concrete adapter.

    Examples:
        mock/echo                  -> MockProvider
        anthropic/claude-sonnet-4-5 -> AnthropicProvider("claude-sonnet-4-5")
        openai/gpt-4o-mini         -> OpenAIProvider("gpt-4o-mini")
    """
    if "/" not in model_spec:
        raise ValueError(f"Expected 'provider/model', got: {model_spec!r}")
    provider, model = model_spec.split("/", 1)
    if provider == "mock":
        return MockProvider()
    if provider == "anthropic":
        return AnthropicProvider(model)
    if provider == "openai":
        return OpenAIProvider(model)
    raise ValueError(f"Unknown provider: {provider!r}")


__all__ = [
    "AnthropicProvider",
    "MockProvider",
    "OpenAIProvider",
    "ProviderAdapter",
    "make_provider",
]
