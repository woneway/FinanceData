from unittest.mock import MagicMock, patch

import pytest

from finance_data.interface.types import DataResult
from finance_data.tool_specs.invoke import ToolInvokeError, canonicalize_tool_params, invoke_tool_spec


def test_invoke_tool_spec_calls_service_target():
    mock_result = DataResult(data=[{"symbol": "000001"}], source="akshare", meta={})
    mock_dispatcher = MagicMock()
    mock_dispatcher.get_realtime_quote.return_value = mock_result
    mock_module = MagicMock(realtime_quote=mock_dispatcher)

    with patch("finance_data.tool_specs.invoke.importlib.import_module", return_value=mock_module):
        invoked = invoke_tool_spec("tool_get_stock_quote_realtime", {"symbol": "000001"})

    assert invoked.result is mock_result
    assert invoked.provider == "akshare"
    assert invoked.source == "service"
    mock_dispatcher.get_realtime_quote.assert_called_once_with(symbol="000001")


def test_invoke_tool_spec_calls_registered_provider():
    mock_result = DataResult(data=[{"symbol": "000001"}], source="tushare", meta={})
    mock_instance = MagicMock()
    mock_instance.get_daily_kline_history.return_value = mock_result
    mock_cls = MagicMock(return_value=mock_instance)

    with patch("finance_data.tool_specs.invoke._import_class", return_value=mock_cls):
        invoked = invoke_tool_spec(
            "tool_get_kline_daily_history",
            {"symbol": "000001", "start": "20260401", "end": "20260402"},
            provider="tushare",
        )

    assert invoked.provider == "tushare"
    assert invoked.source == "provider"
    mock_instance.get_daily_kline_history.assert_called_once_with(
        symbol="000001",
        start="20260401",
        end="20260402",
        adj="qfq",
    )


def test_canonicalize_tool_params_applies_defaults():
    params = canonicalize_tool_params("tool_get_kline_daily_history", {"symbol": "000001"})
    assert params["symbol"] == "000001"
    assert params["start"] == "20240101"
    assert len(params["end"]) == 8
    assert params["adj"] == "qfq"


def test_invoke_tool_spec_rejects_unknown_tool():
    with pytest.raises(ToolInvokeError, match="unknown tool"):
        invoke_tool_spec("not_a_tool", {})


def test_invoke_tool_spec_rejects_missing_required_param():
    with pytest.raises(ToolInvokeError, match="missing required param"):
        invoke_tool_spec("tool_get_stock_quote_realtime", {})


def test_invoke_tool_spec_rejects_unregistered_provider():
    with pytest.raises(ToolInvokeError, match="not registered"):
        invoke_tool_spec("tool_get_stock_quote_realtime", {"symbol": "000001"}, provider="not_real")


def test_invoke_tool_spec_propagates_call_exception():
    mock_dispatcher = MagicMock()
    mock_dispatcher.get_realtime_quote.side_effect = RuntimeError("boom")
    mock_module = MagicMock(realtime_quote=mock_dispatcher)

    with patch("finance_data.tool_specs.invoke.importlib.import_module", return_value=mock_module):
        with pytest.raises(RuntimeError, match="boom"):
            invoke_tool_spec("tool_get_stock_quote_realtime", {"symbol": "000001"})
