from __future__ import annotations

import pytest

from app.agents.test_fix import run_test_fix
from app.schemas import GeneratedTool


class FixingLLM:
    async def generate_json(self, _system_prompt: str, _user_prompt: str):
        return {
            "python_code": "async def execute(**kwargs) -> str:\n    return 'fixed'\n"
        }


@pytest.mark.asyncio
async def test_test_fix_repairs_invalid_code():
    generated = GeneratedTool(
        name="broken_tool",
        description="Broken",
        provider="Example",
        input_schema={"type": "object", "properties": {}},
        python_code="def execute(**kwargs):\n    return 123\n",
    )

    result = await run_test_fix(generated, FixingLLM(), max_attempts=3)

    assert result.success is True
    assert "fixed" in result.final_code
    assert result.attempts == 2
