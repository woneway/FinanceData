from unittest.mock import patch
import json
import asyncio

from finance_data.provider.types import DataResult, DataFetchError

_AKSHARE_RESULT = DataResult(
    data=[{"item": "股票简称", "value": "平安银行"}],
    source="akshare",
    meta={"rows": 1, "symbol": "000001"},
)

_TUSHARE_RESULT = DataResult(
    data=[{"ts_code": "000001.SZ", "name": "平安银行"}],
    source="tushare",
    meta={"rows": 1, "symbol": "000001"},
)


def test_server_importable():
    from finance_data.mcp import server
    assert hasattr(server, "mcp")


def test_only_one_tool_exposed():
    """对外只暴露一个 tool_get_stock_info"""
    from finance_data.mcp import server
    assert hasattr(server, "tool_get_stock_info")
    assert not hasattr(server, "tool_get_stock_info_tushare")


def test_uses_akshare_first():
    """akshare 正常时使用 akshare 结果"""
    from finance_data.mcp.server import tool_get_stock_info

    with patch("finance_data.mcp.server.akshare_get_stock_info", return_value=_AKSHARE_RESULT):
        response = asyncio.run(tool_get_stock_info("000001"))

    parsed = json.loads(response)
    assert parsed["source"] == "akshare"


def test_falls_back_to_tushare_on_akshare_failure():
    """akshare 失败时 fallback 到 tushare"""
    from finance_data.mcp.server import tool_get_stock_info

    with patch("finance_data.mcp.server.akshare_get_stock_info",
               side_effect=DataFetchError("akshare", "stock_individual_info_em", "timeout", "network")), \
         patch("finance_data.mcp.server.tushare_get_stock_info", return_value=_TUSHARE_RESULT):
        response = asyncio.run(tool_get_stock_info("000001"))

    parsed = json.loads(response)
    assert parsed["source"] == "tushare"


def test_returns_error_when_all_providers_fail():
    """所有 provider 都失败时返回错误"""
    from finance_data.mcp.server import tool_get_stock_info

    with patch("finance_data.mcp.server.akshare_get_stock_info",
               side_effect=DataFetchError("akshare", "stock_individual_info_em", "timeout", "network")), \
         patch("finance_data.mcp.server.tushare_get_stock_info",
               side_effect=DataFetchError("tushare", "stock_basic", "auth failed", "auth")):
        response = asyncio.run(tool_get_stock_info("000001"))

    parsed = json.loads(response)
    assert "error" in parsed


def test_tushare_not_tried_when_akshare_succeeds():
    """akshare 成功时不调用 tushare"""
    from finance_data.mcp.server import tool_get_stock_info

    with patch("finance_data.mcp.server.akshare_get_stock_info", return_value=_AKSHARE_RESULT) as mock_ak, \
         patch("finance_data.mcp.server.tushare_get_stock_info") as mock_ts:
        asyncio.run(tool_get_stock_info("000001"))

    mock_ak.assert_called_once()
    mock_ts.assert_not_called()
