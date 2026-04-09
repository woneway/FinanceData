"""Tool metadata projection from the unified ToolSpec registry."""
from __future__ import annotations

from collections import OrderedDict
from typing import Dict, List, Optional

from finance_data.provider.metadata.models import (
    DataFreshness,
    DataSource,
    ToolMeta,
    UpdateTiming,
)
from finance_data.tool_specs import list_tool_specs


_FRESHNESS_MAP = {
    "realtime": DataFreshness.REALTIME,
    "end_of_day": DataFreshness.END_OF_DAY,
    "historical": DataFreshness.HISTORICAL,
    "quarterly": DataFreshness.QUARTERLY,
}

_TIMING_MAP = {
    "T+0": UpdateTiming.T_PLUS_0,
    "T+1_15:30": UpdateTiming.T_PLUS_1_15_30,
    "T+1_16:00": UpdateTiming.T_PLUS_1_16_00,
    "T+1_17:00": UpdateTiming.T_PLUS_1_17_00,
    "next_trade_day_9:30": UpdateTiming.NEXT_TRADE_DAY_9_30,
    "quarterly": UpdateTiming.QUARTERLY_DISCLOSURE,
}

_SOURCE_MAP = {
    "akshare": DataSource.AKSHARE,
    "tencent": DataSource.TENCENT,
    "both": DataSource.BOTH,
    "multi": DataSource.MULTI,
}


def _to_tool_meta(spec) -> ToolMeta:
    meta = spec.metadata
    return ToolMeta(
        name=spec.name,
        description=spec.description,
        domain=spec.domain,
        entity=meta.entity,
        scope=meta.scope,
        data_freshness=_FRESHNESS_MAP[meta.data_freshness],
        update_timing=_TIMING_MAP[meta.update_timing],
        supports_history=meta.supports_history,
        history_start=meta.history_start,
        cache_ttl=meta.cache_ttl,
        source=_SOURCE_MAP.get(meta.source, DataSource.MULTI),
        source_priority=meta.source_priority,
        api_name=meta.api_name,
        limitations=list(meta.limitations),
        return_fields=list(spec.return_fields),
        primary_key=meta.primary_key,
    )


TOOL_REGISTRY: Dict[str, ToolMeta] = OrderedDict(
    (spec.name, _to_tool_meta(spec))
    for spec in list_tool_specs()
)


def get_tool_meta(tool_name: str) -> Optional[ToolMeta]:
    """获取指定工具的元数据"""
    return TOOL_REGISTRY.get(tool_name)


def validate_all_tools() -> Dict[str, List[str]]:
    """
    校验所有工具的元数据完整性

    Returns:
        Dict[str, List[str]]: {tool_name: [error_messages]}
        空 dict 表示全部通过
    """
    errors = {}

    for name, meta in TOOL_REGISTRY.items():
        tool_errors = []

        if not meta.description:
            tool_errors.append("缺少 description")

        if not meta.api_name:
            tool_errors.append("缺少 api_name")

        if not meta.return_fields:
            tool_errors.append("缺少 return_fields")

        if not meta.domain:
            tool_errors.append("缺少 domain")

        if tool_errors:
            errors[name] = tool_errors

    return errors
