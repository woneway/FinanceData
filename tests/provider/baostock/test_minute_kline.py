"""baostock 分钟K线 provider 测试"""
from unittest.mock import patch, MagicMock
import pytest

from finance_data.provider.baostock.kline.minute import BaostockMinuteKline
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return BaostockMinuteKline()


def _mock_rs(rows, error_code="0", error_msg="success"):
    rs = MagicMock()
    rs.error_code = error_code
    rs.error_msg = error_msg
    return rs


def _mock_rows():
    return [
        ["2026-04-17", "20260417093500000", "sz.000001", "11.09", "11.10", "11.06", "11.09", "3563600", "39475806.00"],
        ["2026-04-17", "20260417094000000", "sz.000001", "11.09", "11.09", "11.07", "11.08", "1005483", "11138778.81"],
    ]


def test_returns_data_result(provider):
    mock_bs = MagicMock()
    rs = _mock_rs(_mock_rows())
    mock_bs.query_history_k_data_plus.return_value = rs

    with patch("finance_data.provider.baostock.kline.minute.baostock_session") as mock_ctx, \
         patch("finance_data.provider.baostock.kline.minute.rs_to_list", return_value=_mock_rows()):
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_bs)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
        result = provider.get_minute_kline_history("000001", "5min", "20260417", "20260417")

    assert isinstance(result, DataResult)
    assert result.source == "baostock"
    assert len(result.data) == 2


def test_fields_correct(provider):
    mock_bs = MagicMock()
    rs = _mock_rs(_mock_rows())
    mock_bs.query_history_k_data_plus.return_value = rs

    with patch("finance_data.provider.baostock.kline.minute.baostock_session") as mock_ctx, \
         patch("finance_data.provider.baostock.kline.minute.rs_to_list", return_value=_mock_rows()):
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_bs)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
        result = provider.get_minute_kline_history("000001", "5min", "20260417", "20260417")

    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["date"] == "20260417"
    assert row["time"] == "093500"
    assert row["period"] == "5min"
    assert row["open"] == 11.09
    assert row["close"] == 11.09
    assert row["volume"] == 3563600.0
    assert row["amount"] == 39475806.0
    assert row["adj"] == "qfq"


def test_invalid_period_raises(provider):
    with pytest.raises(DataFetchError) as exc:
        provider.get_minute_kline_history("000001", "1min", "20260417", "20260417")
    assert exc.value.kind == "data"


def test_empty_raises(provider):
    mock_bs = MagicMock()
    rs = _mock_rs([])
    mock_bs.query_history_k_data_plus.return_value = rs

    with patch("finance_data.provider.baostock.kline.minute.baostock_session") as mock_ctx, \
         patch("finance_data.provider.baostock.kline.minute.rs_to_list", return_value=[]):
        mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_bs)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
        with pytest.raises(DataFetchError) as exc:
            provider.get_minute_kline_history("000001", "5min", "20260417", "20260417")
    assert exc.value.kind == "data"


def test_network_error_raises(provider):
    with patch("finance_data.provider.baostock.kline.minute.baostock_session") as mock_ctx:
        mock_ctx.return_value.__enter__ = MagicMock(side_effect=ConnectionError("timeout"))
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
        with pytest.raises(DataFetchError) as exc:
            provider.get_minute_kline_history("000001", "5min", "20260417", "20260417")
    assert exc.value.kind == "network"
