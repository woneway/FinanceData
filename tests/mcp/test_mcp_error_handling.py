"""验证所有 MCP tool 均有错误处理，不会抛出原始异常"""
import asyncio
import json
from unittest.mock import patch
from finance_data.interface.types import DataFetchError, DataResult


def _run(coro):
    return asyncio.run(coro)


def test_daily_kline_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_kline_daily_history
    with patch("finance_data.service.kline.daily_kline_history") as mock:
        mock.get_daily_kline_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_kline_daily_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_weekly_kline_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_kline_weekly_history
    with patch("finance_data.service.kline.weekly_kline_history") as mock:
        mock.get_weekly_kline_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_kline_weekly_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_monthly_kline_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_kline_monthly_history
    with patch("finance_data.service.kline.monthly_kline_history") as mock:
        mock.get_monthly_kline_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_kline_monthly_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_realtime_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_stock_quote_realtime
    with patch("finance_data.service.realtime.realtime_quote") as mock:
        mock.get_realtime_quote.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_stock_quote_realtime("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_index_quote_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_index_quote_realtime
    with patch("finance_data.service.index.index_quote") as mock:
        mock.get_index_quote_realtime.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_index_quote_realtime("000001.SH"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_index_history_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_index_kline_history
    with patch("finance_data.service.index.index_history") as mock:
        mock.get_index_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_index_kline_history("000001.SH"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_board_index_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_board_index_history
    with patch("finance_data.service.board.board_index") as mock:
        mock.get_board_index.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_board_index_history("行业板块"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_board_member_mcp_passes_trade_date():
    from finance_data.mcp.server import tool_get_board_member_history
    with patch("finance_data.service.board.board_member") as mock:
        mock.get_board_member.return_value = DataResult(
            data=[{"symbol": "000001", "name": "Test"}],
            source="tushare",
            meta={},
        )
        result = _run(tool_get_board_member_history("人工智能", "概念板块", trade_date="20260414"))
    parsed = json.loads(result)
    assert parsed["data"][0]["symbol"] == "000001"
    mock.get_board_member.assert_called_once_with(
        board_name="人工智能",
        idx_type="概念板块",
        trade_date="20260414",
        start_date="",
        end_date="",
    )


def test_chip_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_chip_distribution_history
    with patch("finance_data.service.chip.chip_history") as mock:
        mock.get_chip_distribution_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_chip_distribution_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_financial_summary_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_financial_summary_history
    with patch("finance_data.service.fundamental.financial_summary") as mock:
        mock.get_financial_summary_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_financial_summary_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_dividend_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_dividend_history
    with patch("finance_data.service.fundamental.dividend") as mock:
        mock.get_dividend_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_dividend_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


# test_earnings_forecast_mcp_returns_error_json 已移除（tool 已禁用）


def test_cashflow_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_capital_flow_realtime
    with patch("finance_data.service.cashflow.stock_capital_flow") as mock:
        mock.get_stock_capital_flow_realtime.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_capital_flow_realtime("000001"))
    parsed = json.loads(result)
    assert "error" in parsed
