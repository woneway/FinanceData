from unittest.mock import patch
import json
import pytest

from finance_data.provider.types import DataResult, DataFetchError


def test_server_importable():
    """server 模块可以导入"""
    from finance_data.mcp import server
    assert hasattr(server, "mcp")


def test_get_stock_info_tool_success():
    """get_stock_info tool 正常返回 JSON"""
    from finance_data.mcp.server import tool_get_stock_info

    mock_result = DataResult(
        data=[{"item": "股票简称", "value": "平安银行"}],
        source="akshare",
        meta={"rows": 1, "symbol": "000001"},
    )

    with patch("finance_data.mcp.server.get_stock_info", return_value=mock_result):
        import asyncio
        response = asyncio.run(tool_get_stock_info("000001"))

    parsed = json.loads(response)
    assert parsed["source"] == "akshare"
    assert len(parsed["data"]) == 1


def test_get_stock_info_tool_error():
    """get_stock_info tool 错误时返回可读错误信息"""
    from finance_data.mcp.server import tool_get_stock_info

    with patch("finance_data.mcp.server.get_stock_info",
               side_effect=DataFetchError("akshare", "stock_individual_info_em", "timeout", "network")):
        import asyncio
        response = asyncio.run(tool_get_stock_info("000001"))

    assert "错误" in response or "error" in response.lower()
