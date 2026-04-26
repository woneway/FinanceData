"""Unified ToolSpec registry — 按 domain 拆分到 14 个子模块后，由本模块拼接为 OrderedDict。

外部入口仍为：
    from finance_data.tool_specs.registry import TOOL_SPEC_REGISTRY

`_DOMAIN_ORDER` 决定 TOOL_SPEC_REGISTRY 的 keys 顺序；同时也必须与
`mcp/server.py` 中 14 个 tools 子模块的 import 顺序保持一致。两者一致性
由 `tests/mcp/test_tools_layout.py` 守护。
"""
from __future__ import annotations

from collections import OrderedDict

from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry import (  # noqa: I001 — 顺序即注册顺序
    stock,
    kline,
    quote,
    index,
    board,
    fundamental,
    cashflow,
    market,
    lhb,
    pool,
    north_flow,
    margin,
    technical,
    fund_flow,
)

_DOMAIN_ORDER = (
    stock,
    kline,
    quote,
    index,
    board,
    fundamental,
    cashflow,
    market,
    lhb,
    pool,
    north_flow,
    margin,
    technical,
    fund_flow,
)

TOOL_SPEC_REGISTRY: "OrderedDict[str, ToolSpec]" = OrderedDict(
    (spec.name, spec) for module in _DOMAIN_ORDER for spec in module.SPECS
)
