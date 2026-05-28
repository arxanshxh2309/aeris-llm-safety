"""Tests for the provider adapters (mock + factory)."""
from __future__ import annotations

import pytest

from aeris.providers import MockProvider, make_provider


class TestMockProvider:
    @pytest.mark.asyncio
    async def test_returns_response(self) -> None:
        p = MockProvider()
        resp = await p.complete([{"role": "user", "content": "hello"}])
        assert resp.text
        assert resp.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_deterministic(self) -> None:
        p = MockProvider()
        r1 = await p.complete([{"role": "user", "content": "same"}])
        r2 = await p.complete([{"role": "user", "content": "same"}])
        assert r1.text == r2.text


class TestFactory:
    def test_mock(self) -> None:
        p = make_provider("mock/echo")
        assert isinstance(p, MockProvider)

    def test_unknown_provider(self) -> None:
        with pytest.raises(ValueError):
            make_provider("nonexistent/foo")

    def test_missing_slash(self) -> None:
        with pytest.raises(ValueError):
            make_provider("just-a-name")
