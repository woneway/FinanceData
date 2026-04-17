from unittest.mock import patch, MagicMock
import json
import asyncio

from finance_data.interface.types import DataResult, DataFetchError

_AKSHARE_RESULT = DataResult(
    data=[{"symbol": "000001", "name": "平安银行"}],
    source="akshare",
    meta={"rows": 1, "symbol": "000001"},
)

_TUSHARE_RESULT = DataResult(
    data=[{"symbol": "000001", "name": "平安银行"}],
    source="tushare",
    meta={"rows": 1, "symbol": "000001"},
)


def test_server_importable():
    from finance_data.mcp import server
    assert hasattr(server, "mcp")


def test_tool_get_stock_info_history_exposed():
    from finance_data.mcp import server
    assert hasattr(server, "tool_get_stock_info_snapshot")


def test_uses_service_layer():
    """tool 通过 service 层调用，返回正确结果"""
    from finance_data.mcp.server import tool_get_stock_info_snapshot

    with patch("finance_data.mcp.server.stock_history.get_stock_info_history",
               return_value=_AKSHARE_RESULT):
        response = asyncio.run(tool_get_stock_info_snapshot("000001"))

    parsed = json.loads(response)
    assert parsed["source"] == "akshare"


def test_returns_error_when_service_fails():
    from finance_data.mcp.server import tool_get_stock_info_snapshot

    with patch("finance_data.mcp.server.stock_history.get_stock_info_history",
               side_effect=DataFetchError("all", "get_stock_info_history", "所有数据源均失败", "data")):
        response = asyncio.run(tool_get_stock_info_snapshot("000001"))

    parsed = json.loads(response)
    assert "error" in parsed


def test_tool_get_suspend_uses_service_method():
    from finance_data.mcp.server import tool_get_suspend_daily

    with patch(
        "finance_data.mcp.server.suspend.get_suspend_history",
        return_value=_AKSHARE_RESULT,
    ) as mock_method:
        response = asyncio.run(tool_get_suspend_daily("20260408"))

    parsed = json.loads(response)
    assert parsed["source"] == "akshare"
    mock_method.assert_called_once_with(date="20260408")


def test_tool_get_hot_rank_uses_realtime_service_method():
    from finance_data.mcp.server import tool_get_hot_rank_realtime

    with patch(
        "finance_data.mcp.server.hot_rank.get_hot_rank_realtime",
        return_value=_AKSHARE_RESULT,
    ) as mock_method:
        response = asyncio.run(tool_get_hot_rank_realtime())

    parsed = json.loads(response)
    assert parsed["source"] == "akshare"
    mock_method.assert_called_once_with()
