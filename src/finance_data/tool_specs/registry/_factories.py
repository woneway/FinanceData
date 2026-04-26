"""ToolSpec 工厂 helper（供 14 个 domain registry 子模块共享）。"""
from __future__ import annotations

from typing import Any

from finance_data.tool_specs.models import (
    ProbeSpec,
    ProviderSpec,
    ServiceTargetSpec,
    ToolMetadataSpec,
    ToolParamChoice,
    ToolParamSpec,
)


def _param(
    name: str,
    *,
    required: bool,
    default: Any = None,
    description: str = "",
    example: Any = None,
    aliases: tuple[str, ...] = (),
    choices: tuple[tuple[Any, str], ...] = (),
) -> ToolParamSpec:
    return ToolParamSpec(
        name=name,
        required=required,
        default=default,
        description=description,
        example=example,
        aliases=aliases,
        choices=tuple(ToolParamChoice(value=value, label=label) for value, label in choices),
    )


def _provider(
    name: str,
    class_path: str,
    method_name: str,
    *,
    available_if: str = "",
    notes: str = "",
) -> ProviderSpec:
    return ProviderSpec(
        name=name,
        class_path=class_path,
        method_name=method_name,
        available_if=available_if,
        notes=notes,
    )


def _service(module_path: str, object_name: str, method_name: str) -> ServiceTargetSpec:
    return ServiceTargetSpec(
        module_path=module_path,
        object_name=object_name,
        method_name=method_name,
    )


def _probe(
    default_params: dict[str, Any],
    *,
    timeout_sec: int = 30,
    min_records: int = 0,
    required_fields: tuple[str, ...] = (),
    consistency_enabled: bool = True,
) -> ProbeSpec:
    return ProbeSpec(
        default_params=default_params,
        timeout_sec=timeout_sec,
        min_records=min_records,
        required_fields=required_fields,
        consistency_enabled=consistency_enabled,
    )


def _meta(
    *,
    entity: str,
    scope: str,
    data_freshness: str,
    update_timing: str,
    supports_history: bool,
    history_start: str | None = None,
    cache_ttl: int = 0,
    source: str = "both",
    source_priority: str = "akshare",
    api_name: str = "",
    limitations: tuple[str, ...] = (),
    primary_key: str = "date",
    examples: tuple[dict[str, Any], ...] = (),
) -> ToolMetadataSpec:
    return ToolMetadataSpec(
        entity=entity,
        scope=scope,
        data_freshness=data_freshness,
        update_timing=update_timing,
        supports_history=supports_history,
        history_start=history_start,
        cache_ttl=cache_ttl,
        source=source,
        source_priority=source_priority,
        api_name=api_name,
        limitations=limitations,
        primary_key=primary_key,
        examples=examples,
    )
