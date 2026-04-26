"""守护测试：FinanceData 客户端方法名 = MCP tool 名（去 `tool_get_` 前缀）。

实现 `client-naming` capability 的：
- 「客户端公开方法名必须从 MCP tool 名派生」Requirement
- 「客户端方法重命名必须保留 deprecated alias」Requirement
- 「客户端命名一致性必须由守护测试强制」Requirement
"""
from __future__ import annotations

import warnings

import pytest

from finance_data import FinanceData
from finance_data.tool_specs.registry import TOOL_SPEC_REGISTRY


_TOOL_PREFIX = "tool_get_"


def _expected_method_names() -> set[str]:
    """从 MCP tool 名集合派生期望的客户端方法名集合。"""
    return {
        name[len(_TOOL_PREFIX):]
        for name in TOOL_SPEC_REGISTRY.keys()
    }


def _client_public_methods() -> set[str]:
    """枚举 FinanceData 公开方法（排除以 _ 开头 + 排除 alias 旧名）。"""
    fd = FinanceData()
    aliases = getattr(FinanceData, "_DEPRECATED_ALIASES", {})
    return {
        m for m in dir(fd)
        if not m.startswith("_")
        and m not in aliases
        and callable(getattr(fd, m, None))
    }


def test_client_methods_match_mcp_tools_as_set() -> None:
    """集合一致性：客户端公开方法集合 = MCP tool 名集合（去 tool_get_ 前缀）。"""
    expected = _expected_method_names()
    actual = _client_public_methods()

    only_in_expected = expected - actual
    only_in_actual = actual - expected

    assert not only_in_expected and not only_in_actual, (
        f"FinanceData 公开方法名与 MCP tool 名（去 tool_get_ 前缀）不一致。\n"
        f"  仅在 MCP（client 缺少）: {sorted(only_in_expected)}\n"
        f"  仅在 client（MCP 缺少）: {sorted(only_in_actual)}\n"
        f"  client 方法名应严格 = MCP tool 名去 `tool_get_` 前缀。"
    )


def test_deprecated_aliases_are_callable_and_warn() -> None:
    """所有 deprecated alias 旧名都能调用并触发 DeprecationWarning。"""
    aliases = getattr(FinanceData, "_DEPRECATED_ALIASES", None)
    assert aliases is not None, (
        "FinanceData 类未定义 _DEPRECATED_ALIASES 字典。"
        "请在 client.py 顶部加入 deprecated 旧名 → 新名的映射字典。"
    )
    assert isinstance(aliases, dict) and len(aliases) > 0, (
        "_DEPRECATED_ALIASES 必须是非空 dict。"
    )

    fd = FinanceData()
    failures: list[str] = []
    for old_name, new_name in aliases.items():
        # 1. 新名必须存在为方法
        if not callable(getattr(fd, new_name, None)):
            failures.append(f"alias 新名 `{new_name}` 在 FinanceData 上不存在或不可调用")
            continue
        # 2. 旧名 getattr 必须发出 DeprecationWarning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                attr = getattr(fd, old_name)
            except AttributeError as e:
                failures.append(f"alias 旧名 `{old_name}` getattr 抛 AttributeError: {e}")
                continue
            if not callable(attr):
                failures.append(f"alias 旧名 `{old_name}` 解析后非可调用对象")
                continue
            dep_warnings = [
                wi for wi in w
                if issubclass(wi.category, DeprecationWarning)
                and old_name in str(wi.message)
            ]
            if not dep_warnings:
                failures.append(
                    f"alias 旧名 `{old_name}` 未触发含旧名的 DeprecationWarning"
                )

    assert not failures, "alias 守护失败：\n  " + "\n  ".join(failures)


def test_alias_keys_do_not_overlap_with_real_methods() -> None:
    """alias 旧名不能与新方法名冲突，否则 alias 拦截器永远不会被触发。"""
    aliases = getattr(FinanceData, "_DEPRECATED_ALIASES", {})
    real_methods = _client_public_methods()
    overlap = set(aliases.keys()) & real_methods
    assert not overlap, (
        f"alias 旧名与新方法名冲突：{sorted(overlap)}\n"
        f"alias 旧名必须是已被重命名的「不再存在」的名字。"
    )
