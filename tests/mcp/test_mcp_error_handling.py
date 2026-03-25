"""验证所有 MCP tool 均有错误处理，不会抛出原始异常"""
import asyncio
import json
from unittest.mock import patch
from finance_data.interface.types import DataFetchError


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_kline_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_kline_history
    with patch("finance_data.mcp.server.kline_history") as mock:
        mock.get_kline_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_kline_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_realtime_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_realtime_quote
    with patch("finance_data.mcp.server.realtime_quote") as mock:
        mock.get_realtime_quote.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_realtime_quote("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_index_quote_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_index_quote_realtime
    with patch("finance_data.mcp.server.index_quote") as mock:
        mock.get_index_quote_realtime.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_index_quote_realtime("000001.SH"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_index_history_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_index_history
    with patch("finance_data.mcp.server.index_history") as mock:
        mock.get_index_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_index_history("000001.SH"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_sector_rank_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_sector_rank_realtime
    with patch("finance_data.mcp.server.sector_rank") as mock:
        mock.get_sector_rank_realtime.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_sector_rank_realtime())
    parsed = json.loads(result)
    assert "error" in parsed


def test_chip_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_chip_distribution_history
    with patch("finance_data.mcp.server.chip_history") as mock:
        mock.get_chip_distribution_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_chip_distribution_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_financial_summary_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_financial_summary_history
    with patch("finance_data.mcp.server.financial_summary") as mock:
        mock.get_financial_summary_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_financial_summary_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_dividend_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_dividend_history
    with patch("finance_data.mcp.server.dividend") as mock:
        mock.get_dividend_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_dividend_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_earnings_forecast_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_earnings_forecast_history
    with patch("finance_data.mcp.server.earnings_forecast") as mock:
        mock.get_earnings_forecast_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_earnings_forecast_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_cashflow_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_stock_capital_flow_realtime
    with patch("finance_data.mcp.server.stock_capital_flow") as mock:
        mock.get_stock_capital_flow_realtime.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_stock_capital_flow_realtime("000001"))
    parsed = json.loads(result)
    assert "error" in parsed
