"""Adapters for reading ToolSpec registry."""
from __future__ import annotations

import datetime
from typing import Any

from finance_data.tool_specs.models import ProbeSpec, ProviderSpec, ServiceTargetSpec, ToolParamSpec, ToolSpec
from finance_data.tool_specs.registry import TOOL_SPEC_REGISTRY


def get_tool_spec(name: str) -> ToolSpec | None:
    return TOOL_SPEC_REGISTRY.get(name)


def list_tool_specs() -> list[ToolSpec]:
    return list(TOOL_SPEC_REGISTRY.values())


def get_tool_params(name: str) -> tuple[ToolParamSpec, ...]:
    spec = get_tool_spec(name)
    return spec.params if spec else ()


def get_tool_service_target(name: str) -> ServiceTargetSpec | None:
    spec = get_tool_spec(name)
    return spec.service if spec else None


def get_tool_providers(name: str) -> tuple[ProviderSpec, ...]:
    spec = get_tool_spec(name)
    return spec.providers if spec else ()


def get_tool_probe(name: str) -> ProbeSpec | None:
    spec = get_tool_spec(name)
    return spec.probe if spec else None


def normalize_tool_params(name: str, params: dict[str, Any]) -> dict[str, Any]:
    """Rewrite canonical param names to provider-level aliases.

    ToolParamSpec.name is the MCP-facing canonical name (e.g. ``sector_name``).
    ToolParamSpec.aliases lists the names that provider methods actually accept
    (e.g. ``("symbol",)``).  This function rewrites canonical → alias so that
    the resulting dict can be passed directly to a provider method.
    """
    spec = get_tool_spec(name)
    if spec is None:
        return dict(params)

    normalized = dict(params)
    for param in spec.params:
        for alias in param.aliases:
            if param.name in normalized and alias not in normalized:
                normalized[alias] = normalized.pop(param.name)
                break
    return normalized


def apply_tool_defaults(name: str, params: dict[str, Any]) -> dict[str, Any]:
    """Fill missing optional params from ToolSpec and resolve dynamic date defaults."""
    spec = get_tool_spec(name)
    if spec is None:
        return dict(params)

    resolved = dict(params)
    for param in spec.params:
        if param.name in resolved:
            continue
        if param.required or param.default is None:
            continue
        value = param.default
        if param.name == "end" and value == "":
            value = datetime.date.today().strftime("%Y%m%d")
        resolved[param.name] = value
    return resolved
