"""跨 Provider 数据一致性比较引擎"""
from typing import Any, Dict, List, Optional, Set

from finance_data.dashboard.models import ConsistencyResult, FieldDiff
from finance_data.provider.metadata.registry import TOOL_REGISTRY

# 始终跳过的字段（不同 provider 天然不同）
_ALWAYS_SKIP: Set[str] = {"source", "timestamp"}

# Per-tool 跳过字段（已知跨源差异，非 bug）
_TOOL_SKIP: Dict[str, Set[str]] = {
    "tool_get_index_kline_history": {"amount"},       # 新浪源不提供成交额，固定为 0
    "tool_get_index_quote_realtime": {"name"},   # xueqiu API 对指数不返回 name
}

# 数值容差
_RELATIVE_TOL = 0.01   # 1%
_ABSOLUTE_TOL = 0.01


def compare_provider_data(
    tool_name: str,
    provider_data: Dict[str, List[Dict[str, Any]]],
) -> Optional[ConsistencyResult]:
    """比较多个 provider 对同一 tool 的返回数据。

    Args:
        tool_name: tool 名称
        provider_data: {provider_name: data_rows}，仅包含探测成功的 provider

    Returns:
        ConsistencyResult（2+ provider 时），否则 None
    """
    providers = list(provider_data.keys())
    if len(providers) < 2:
        return None

    record_counts = {p: len(rows) for p, rows in provider_data.items()}
    diffs: List[FieldDiff] = []

    # 记录数不一致 → warn
    counts = list(record_counts.values())
    if len(set(counts)) > 1:
        diffs.append(FieldDiff(
            field="__record_count__",
            level="warn",
            detail=f"记录数不一致",
            values={p: c for p, c in record_counts.items()},
        ))

    # 获取主键用于行匹配
    meta = TOOL_REGISTRY.get(tool_name)
    primary_key = meta.primary_key if meta else "date"

    # 匹配行并比较
    tool_skip = _TOOL_SKIP.get(tool_name, set())
    matched = _match_rows(provider_data, primary_key, max_compare=5)
    for row_key, provider_rows in matched.items():
        row_diffs = _compare_single_row(providers, provider_rows, row_key, tool_skip)
        diffs.extend(row_diffs)

    # 确定最差等级
    if not diffs:
        status = "consistent"
    elif any(d.level == "error" for d in diffs):
        status = "error"
    else:
        status = "warn"

    return ConsistencyResult(
        tool=tool_name,
        providers_compared=providers,
        status=status,
        record_counts=record_counts,
        diffs=diffs,
    )


def _match_rows(
    provider_data: Dict[str, List[Dict[str, Any]]],
    primary_key: str,
    max_compare: int = 5,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """按主键匹配跨 provider 的行。

    Returns: {row_key: {provider: row_dict}}
    """
    providers = list(provider_data.keys())

    # 所有 provider 都只有 1 行 → 直接比较
    if all(len(rows) == 1 for rows in provider_data.values()):
        return {"row_0": {p: rows[0] for p, rows in provider_data.items()}}

    key_fields = [f.strip() for f in primary_key.split(",") if f.strip()]
    if not key_fields:
        key_fields = [primary_key]

    # 多行：按 primary_key 索引，支持逗号分隔的复合主键。
    indexed: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for provider, rows in provider_data.items():
        for row in rows:
            key_parts = [str(row.get(field, "")) for field in key_fields]
            if any(not part for part in key_parts):
                continue
            key_val = "|".join(key_parts)
            indexed.setdefault(key_val, {})[provider] = row

    # 仅保留所有 provider 都有的行
    common_keys = [
        k for k, v in indexed.items()
        if len(v) == len(providers)
    ][:max_compare]

    return {k: indexed[k] for k in common_keys}


def _compare_single_row(
    providers: List[str],
    provider_rows: Dict[str, Dict[str, Any]],
    row_key: str,
    tool_skip: Set[str] = frozenset(),
) -> List[FieldDiff]:
    """比较一组匹配行的所有字段。"""
    diffs: List[FieldDiff] = []

    # 收集所有字段名
    all_fields: Set[str] = set()
    for row in provider_rows.values():
        all_fields.update(row.keys())

    suffix = "" if row_key == "row_0" else f" ({row_key})"

    for field in sorted(all_fields):
        if field in _ALWAYS_SKIP or field in tool_skip:
            continue

        values = {p: provider_rows[p].get(field) for p in providers}

        has_value = {p for p, v in values.items() if _is_present(v)}
        missing_value = set(providers) - has_value

        if not has_value:
            continue  # 都为空

        if missing_value and has_value:
            diffs.append(FieldDiff(
                field=f"{field}{suffix}",
                level="warn",
                detail=f"{', '.join(sorted(missing_value))} 缺失; {', '.join(sorted(has_value))} 有值",
                values=values,
            ))
            continue

        # 所有 provider 都有值，检查一致性
        present_values = [values[p] for p in providers]
        if _values_consistent(present_values):
            continue

        diffs.append(FieldDiff(
            field=f"{field}{suffix}",
            level="error",
            detail="值不一致",
            values=values,
        ))

    return diffs


def _is_present(value: Any) -> bool:
    """判断值是否"有效"（非 None、非空字符串）。"""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    return True


def _values_consistent(values: List[Any]) -> bool:
    """判断一组值是否一致（数值用容差，字符串精确比较）。"""
    if len(values) < 2:
        return True

    # 全部是数值
    if all(isinstance(v, (int, float)) for v in values):
        return _numeric_consistent(values)

    # 字符串比较（strip + lower）
    str_vals = [str(v).strip().lower() for v in values]
    return len(set(str_vals)) == 1


def _numeric_consistent(values: List[float]) -> bool:
    """数值容差比较：相对 1% 或绝对 0.01，取较大值。"""
    if not values:
        return True
    max_abs = max(abs(v) for v in values)
    threshold = max(_ABSOLUTE_TOL, max_abs * _RELATIVE_TOL)
    base = values[0]
    return all(abs(v - base) <= threshold for v in values[1:])
