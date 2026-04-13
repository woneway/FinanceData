"""验证 MCP 工具的默认日期不是硬编码的过期值"""
import inspect
from finance_data.mcp.server import (
    tool_get_kline_daily_history,
    tool_get_kline_weekly_history,
    tool_get_kline_monthly_history,
    tool_get_index_kline_history,
)


def test_daily_kline_end_not_hardcoded():
    """daily kline end 参数不应硬编码为 20241231"""
    sig = inspect.signature(tool_get_kline_daily_history)
    end_default = sig.parameters["end"].default
    assert end_default != "20241231", f"end 默认值不应硬编码为过期日期: {end_default}"


def test_weekly_kline_end_not_hardcoded():
    """weekly kline end 参数不应硬编码为 20241231"""
    sig = inspect.signature(tool_get_kline_weekly_history)
    end_default = sig.parameters["end"].default
    assert end_default != "20241231", f"end 默认值不应硬编码为过期日期: {end_default}"


def test_monthly_kline_end_not_hardcoded():
    """monthly kline end 参数不应硬编码为 20241231"""
    sig = inspect.signature(tool_get_kline_monthly_history)
    end_default = sig.parameters["end"].default
    assert end_default != "20241231", f"end 默认值不应硬编码为过期日期: {end_default}"


def test_index_history_end_not_hardcoded():
    """index_history end 参数不应硬编码为 20241231"""
    sig = inspect.signature(tool_get_index_kline_history)
    end_default = sig.parameters["end"].default
    assert end_default != "20241231", f"end 默认值不应硬编码为过期日期: {end_default}"
