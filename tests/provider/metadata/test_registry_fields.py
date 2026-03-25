"""验证 registry return_fields 不包含 pct_change（应为 pct_chg）"""
from finance_data.provider.metadata.registry import TOOL_REGISTRY


def test_no_pct_change_in_return_fields():
    """所有 return_fields 中不应出现 pct_change，应为 pct_chg"""
    violations = []
    for name, meta in TOOL_REGISTRY.items():
        if "pct_change" in meta.return_fields:
            violations.append(name)
    assert not violations, f"以下工具 return_fields 含 pct_change（应为 pct_chg）: {violations}"
