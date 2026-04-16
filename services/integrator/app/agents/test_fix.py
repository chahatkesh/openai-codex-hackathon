from __future__ import annotations

import asyncio
import importlib.util
import tempfile
from pathlib import Path

from app.llm import LLMClient
from app.schemas import GeneratedTool, TestResult

FIX_PROMPT = """You fix Python async tool code. Return strict JSON with a single key `python_code`.
The code must define `async def execute(**kwargs) -> str`.
"""


async def _run_execute_from_file(path: Path) -> str:
    module_name = f"generated_tool_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not spec or not spec.loader:
        raise RuntimeError("Failed to load generated module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    execute = getattr(module, "execute", None)
    if execute is None:
        raise RuntimeError("Generated code missing execute function")

    result = execute(sample="healthcheck")
    if asyncio.iscoroutine(result):
        result = await result
    if not isinstance(result, str):
        raise RuntimeError("execute() must return a string")
    return result


async def run_test_fix(tool: GeneratedTool, llm: LLMClient, max_attempts: int = 3) -> TestResult:
    current_code = tool.python_code
    errors: list[str] = []

    for attempt in range(1, max_attempts + 1):
        with tempfile.TemporaryDirectory(prefix="fusekit_tool_test_") as tmp:
            path = Path(tmp) / f"{tool.name}.py"
            path.write_text(current_code, encoding="utf-8")
            try:
                await _run_execute_from_file(path)
                return TestResult(success=True, final_code=current_code, attempts=attempt)
            except Exception as exc:
                errors.append(f"attempt {attempt}: {exc}")
                if attempt == max_attempts:
                    break

        fix_input = (
            f"Tool name: {tool.name}\n"
            f"Current code:\n{current_code}\n\n"
            f"Error:\n{errors[-1]}"
        )
        fixed = await llm.generate_json(FIX_PROMPT, fix_input)
        proposed = fixed.get("python_code")
        if isinstance(proposed, str) and proposed.strip():
            current_code = proposed

    return TestResult(
        success=False,
        final_code=current_code,
        attempts=max_attempts,
        error_log="\n".join(errors)[:2000],
    )
