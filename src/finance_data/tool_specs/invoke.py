"""Shared ToolSpec-based invocation for delivery layers."""
from __future__ import annotations

import importlib
import time
from dataclasses import dataclass
from typing import Any

from finance_data.interface.types import DataResult
from finance_data.tool_specs.adapters import apply_tool_defaults, get_tool_spec, normalize_tool_params


@dataclass(frozen=True)
class ToolInvokeResult:
    tool: str
    result: DataResult
    provider: str
    response_time_ms: float
    params: dict[str, Any]
    source: str


class ToolInvokeError(ValueError):
    """Raised when a ToolSpec delivery invocation cannot be performed."""


def _import_class(class_path: str):
    if ":" not in class_path:
        raise ToolInvokeError(f"invalid provider class path: {class_path}")
    module_path, class_name = class_path.split(":", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def canonicalize_tool_params(tool: str, params: dict[str, Any]) -> dict[str, Any]:
    """Resolve aliases, apply defaults, and validate required params."""
    spec = get_tool_spec(tool)
    if spec is None:
        raise ToolInvokeError(f"unknown tool: {tool}")

    canonical = dict(params)
    for param in spec.params:
        if param.name in canonical:
            continue
        for alias in param.aliases:
            if alias in canonical:
                canonical[param.name] = canonical.pop(alias)
                break

    canonical = apply_tool_defaults(tool, canonical)
    for param in spec.params:
        if param.required and param.name not in canonical:
            raise ToolInvokeError(f"missing required param '{param.name}'")
    return canonical


def invoke_tool_spec(
    tool: str,
    params: dict[str, Any],
    provider: str | None = None,
) -> ToolInvokeResult:
    """Invoke a registered tool through its ToolSpec service or provider target."""
    spec = get_tool_spec(tool)
    if spec is None:
        raise ToolInvokeError(f"unknown tool: {tool}")

    canonical_params = canonicalize_tool_params(tool, params)
    call_params = normalize_tool_params(tool, canonical_params)

    start = time.monotonic()
    if provider:
        matched = [p for p in spec.providers if p.name == provider]
        if not matched:
            raise ToolInvokeError(f"provider '{provider}' not registered for {tool}")
        provider_spec = matched[0]
        cls = _import_class(provider_spec.class_path)
        result = getattr(cls(), provider_spec.method_name)(**call_params)
        actual_provider = provider
        source = "provider"
    else:
        target = spec.service
        if target is None:
            raise ToolInvokeError(f"service target not found for {tool}")
        module = importlib.import_module(target.module_path)
        dispatcher = getattr(module, target.object_name)
        result = getattr(dispatcher, target.method_name)(**call_params)
        actual_provider = result.source
        source = "service"

    elapsed = round((time.monotonic() - start) * 1000, 1)
    return ToolInvokeResult(
        tool=tool,
        result=result,
        provider=actual_provider,
        response_time_ms=elapsed,
        params=call_params,
        source=source,
    )
