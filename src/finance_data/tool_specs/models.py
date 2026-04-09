"""Unified tool specification models."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolParamSpec:
    name: str
    required: bool
    default: Any = None
    description: str = ""
    example: Any = None
    aliases: tuple[str, ...] = ()

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "required": self.required,
            "default": self.default,
        }


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    class_path: str
    method_name: str
    available_if: str = ""
    notes: str = ""


@dataclass(frozen=True)
class ServiceTargetSpec:
    module_path: str
    object_name: str
    method_name: str


@dataclass(frozen=True)
class ProbeSpec:
    default_params: dict[str, Any] = field(default_factory=dict)
    timeout_sec: int = 30
    min_records: int = 0
    required_fields: tuple[str, ...] = ()
    consistency_enabled: bool = True


@dataclass(frozen=True)
class ToolMetadataSpec:
    entity: str
    scope: str
    data_freshness: str
    update_timing: str
    supports_history: bool
    history_start: str | None = None
    cache_ttl: int = 0
    source: str = "both"
    source_priority: str = "akshare"
    api_name: str = ""
    limitations: tuple[str, ...] = ()
    primary_key: str = "date"
    examples: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    domain: str
    params: tuple[ToolParamSpec, ...]
    return_fields: tuple[str, ...]
    service: ServiceTargetSpec
    providers: tuple[ProviderSpec, ...]
    probe: ProbeSpec
    metadata: ToolMetadataSpec

