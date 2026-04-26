"""守护测试：MCP 注册的 tool 列表必须与 TOOL_SPEC_REGISTRY 完全一致。

实现 `delivery-tool-spec-contract` 的：
- 「MCP tool 注册顺序必须与 ToolSpec registry 顺序严格一致」Requirement
- 「拆分必须保留外部 import 入口与测试 mock 路径」Requirement

锁定不变量：mcp 实例注册的 tool 名称列表（按 `mcp.list_tools()` 顺序）
== TOOL_SPEC_REGISTRY OrderedDict 的 keys 列表。

未来任何拆分 / 合并 / 新增 tool 都必须保持这两个列表完全相等（集合 + 顺序），
否则下游 dashboard / cli 工具列表展示会与 ToolSpec 注册表漂移。
"""
from __future__ import annotations

import asyncio


def _registered_tool_names() -> list[str]:
    """枚举 mcp 已注册的 48 个 tool 名称（按注册顺序）。"""
    from finance_data.mcp.server import mcp

    tools = asyncio.run(mcp.list_tools())
    return [t.name for t in tools]


def _registry_tool_names() -> list[str]:
    """枚举 TOOL_SPEC_REGISTRY 的 48 个 ToolSpec 名称（按 OrderedDict keys 顺序）。"""
    from finance_data.tool_specs.registry import TOOL_SPEC_REGISTRY

    return list(TOOL_SPEC_REGISTRY.keys())


def test_mcp_and_registry_tool_names_match_as_set() -> None:
    """集合一致性：mcp 注册的 tool 集合 = TOOL_SPEC_REGISTRY keys 集合。"""
    mcp_names = set(_registered_tool_names())
    registry_names = set(_registry_tool_names())

    only_in_mcp = mcp_names - registry_names
    only_in_registry = registry_names - mcp_names

    assert not only_in_mcp and not only_in_registry, (
        f"MCP 与 ToolSpec registry 集合不一致。\n"
        f"  仅在 MCP: {sorted(only_in_mcp)}\n"
        f"  仅在 registry: {sorted(only_in_registry)}\n"
        f"  请确保每个 ToolSpec 都有对应 @mcp.tool 函数，反之亦然。"
    )


def test_mcp_and_registry_tool_names_match_as_list() -> None:
    """顺序一致性：mcp 注册顺序 = TOOL_SPEC_REGISTRY keys 顺序。"""
    mcp_list = _registered_tool_names()
    registry_list = _registry_tool_names()

    if mcp_list == registry_list:
        return

    # 给出第一处不一致的具体位置以便定位
    first_diff = next(
        (i for i, (a, b) in enumerate(zip(mcp_list, registry_list)) if a != b),
        min(len(mcp_list), len(registry_list)),
    )
    raise AssertionError(
        f"MCP 与 ToolSpec registry 顺序不一致，首处差异在索引 {first_diff}：\n"
        f"  MCP[{first_diff}]      = {mcp_list[first_diff] if first_diff < len(mcp_list) else '<缺失>'}\n"
        f"  registry[{first_diff}] = {registry_list[first_diff] if first_diff < len(registry_list) else '<缺失>'}\n"
        f"  请检查 mcp/tools/__init__.py 与 tool_specs/registry/__init__.py 的 _DOMAIN_ORDER 是否对齐。"
    )


def test_tool_count_is_48() -> None:
    """元测试：当前固定 48 个 tool；新增 / 删除时必须同步更新此断言（防止意外增减）。"""
    mcp_count = len(_registered_tool_names())
    registry_count = len(_registry_tool_names())
    assert mcp_count == registry_count == 48, (
        f"期望 48 个 tool，实际 mcp={mcp_count} / registry={registry_count}。"
        f"如果是有意增减，请同步更新此断言。"
    )
