from unittest.mock import patch
import json
import asyncio
import pytest

from finance_data.provider.types import DataResult, DataFetchError


def test_server_importable():
    """server 模块可以导入"""
    from finance_data.mcp import server
    assert hasattr(server, "mcp")


def test_get_stock_info_tool_success():
    """akshare tool 正常返回 JSON"""
    from finance_data.mcp.server import tool_get_stock_info

    mock_result = DataResult(
        data=[{"item": "股票简称", "value": "平安银行"}],
        source="akshare",
        meta={"rows": 1, "symbol": "000001"},
    )

    with patch("finance_data.mcp.server.akshare_get_stock_info", return_value=mock_result):
        response = asyncio.run(tool_get_stock_info("000001"))

    parsed = json.loads(response)
    assert parsed["source"] == "akshare"
    assert len(parsed["data"]) == 1


def test_get_stock_info_tool_error():
    """akshare tool 错误时返回可读错误信息"""
    from finance_data.mcp.server import tool_get_stock_info

    with patch("finance_data.mcp.server.akshare_get_stock_info",
               side_effect=DataFetchError("akshare", "stock_individual_info_em", "timeout", "network")):
        response = asyncio.run(tool_get_stock_info("000001"))

    assert "错误" in response or "error" in response.lower()


def test_get_stock_info_tushare_tool_success():
    """tushare tool 正常返回 JSON"""
    from finance_data.mcp.server import tool_get_stock_info_tushare

    mock_result = DataResult(
        data=[{"ts_code": "000001.SZ", "name": "平安银行", "industry": "银行"}],
        source="tushare",
        meta={"rows": 1, "symbol": "000001"},
    )

    with patch("finance_data.mcp.server.tushare_get_stock_info", return_value=mock_result):
        response = asyncio.run(tool_get_stock_info_tushare("000001"))

    parsed = json.loads(response)
    assert parsed["source"] == "tushare"
    assert parsed["data"][0]["name"] == "平安银行"


def test_get_stock_info_tushare_tool_auth_error():
    """tushare tool auth 错误时返回可读错误信息"""
    from finance_data.mcp.server import tool_get_stock_info_tushare

    with patch("finance_data.mcp.server.tushare_get_stock_info",
               side_effect=DataFetchError("tushare", "init", "TUSHARE_TOKEN 未设置", "auth")):
        response = asyncio.run(tool_get_stock_info_tushare("000001"))

    parsed = json.loads(response)
    assert parsed["kind"] == "auth"
