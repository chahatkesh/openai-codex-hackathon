"""Tool registry — loads and dispatches tool implementations."""

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Any, Callable, Coroutine

logger = logging.getLogger("fusekit.registry")

# Map of tool_name -> async execute function
_registry: dict[str, Callable[..., Coroutine[Any, Any, str]]] = {}

# Directory where the integrator drops dynamically generated tool files
DYNAMIC_TOOLS_DIR = Path("/tmp/fusekit_dynamic_tools")


def register(name: str, func: Callable[..., Coroutine[Any, Any, str]]) -> None:
    _registry[name] = func


def get_executor(name: str) -> Callable[..., Coroutine[Any, Any, str]] | None:
    return _registry.get(name)


def load_dynamic(name: str) -> Callable[..., Coroutine[Any, Any, str]] | None:
    """Try to load a pipeline-generated tool from the dynamic tools directory.

    If the file exists and exports an `execute` function, register it and
    return it so subsequent calls skip the file-system lookup.
    """
    tool_file = DYNAMIC_TOOLS_DIR / f"{name}.py"
    if not tool_file.exists():
        return None

    try:
        module_name = f"fusekit_dynamic_{name}"
        spec = importlib.util.spec_from_file_location(module_name, tool_file)
        if spec is None or spec.loader is None:
            logger.warning("dynamic_load_no_spec name=%s", name)
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        executor = getattr(module, "execute", None)
        if executor is None or not callable(executor):
            logger.warning("dynamic_load_no_execute name=%s", name)
            return None

        # Cache in registry so future calls are instant
        _registry[name] = executor
        logger.info("dynamic_tool_loaded name=%s", name)
        return executor

    except Exception as exc:
        logger.error("dynamic_load_failed name=%s error=%s", name, exc)
        return None


def load_all() -> None:
    """Import all built-in tool modules to trigger registration."""
    modules = [
        "app.tools.scrape_url",
        "app.tools.send_email",
        "app.tools.send_sms",
        "app.tools.search_web",
        "app.tools.get_producthunt",
        "app.tools.get_capability_manifest",
        "app.tools.request_integration",
    ]
    for mod in modules:
        importlib.import_module(mod)
