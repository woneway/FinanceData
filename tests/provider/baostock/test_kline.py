"""baostock K线测试"""
from unittest.mock import patch, MagicMock
import pytest
from finance_data.provider.baostock.kline.history import BaostockKlineHistory
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return BaostockKlineHistory()


@pytest.fixture
def mock_rs():
    """模拟 baostock ResultData"""
    rs = MagicMock()
    rs.error_code = "0"
    rs.fields = ["date", "code", "open", "high", "low", "close", "volume", "amount"]
    rs._data = [
        ["2026-04-01", "sz.000001", "11.09", "11.23", "11.08", "11.15", "91892539", "1025538832.67"],
        ["2026-04-02", "sz.000001", "11.15", "11.30", "11.10", "11.22", "85000000", "950000000.00"],
    ]
    rs._idx = 0

    def _next():
        if rs._idx < len(rs._data):
            return True
        return False

    def _get_row():
        row = rs._data[rs._idx]
        rs._idx += 1
        return row

    rs.next = _next
    rs.get_row_data = _get_row
    return rs


def _mock_session(mock_rs):
    """Create a mock baostock_session context manager"""
    from contextlib import contextmanager

    @contextmanager
    def _session():
        bs_mock = MagicMock()
        bs_mock.query_history_k_data_plus.return_value = mock_rs
        yield bs_mock

    return _session


def test_returns_data_result(provider, mock_rs):
    with patch("finance_data.provider.baostock.kline.history.baostock_session", _mock_session(mock_rs)):
        result = provider.get_kline_history("000001", "daily", "20260401", "20260402", "qfq")
    assert isinstance(result, DataResult)
    assert result.source == "baostock"
    assert len(result.data) == 2


def test_fields_correct(provider, mock_rs):
    with patch("finance_data.provider.baostock.kline.history.baostock_session", _mock_session(mock_rs)):
        result = provider.get_kline_history("000001", "daily", "20260401", "20260402", "qfq")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["date"] == "20260401"
    assert row["open"] == 11.09
    assert row["close"] == 11.15
    assert row["volume"] == 91892539.0
    assert row["amount"] == 1025538832.67


def test_empty_raises(provider):
    from contextlib import contextmanager

    @contextmanager
    def _empty_session():
        bs_mock = MagicMock()
        rs = MagicMock()
        rs.error_code = "0"
        rs.next = lambda: False
        bs_mock.query_history_k_data_plus.return_value = rs
        yield bs_mock

    with patch("finance_data.provider.baostock.kline.history.baostock_session", _empty_session):
        with pytest.raises(DataFetchError) as exc:
            provider.get_kline_history("000001", "daily", "20260401", "20260402", "qfq")
    assert exc.value.kind == "data"


def test_unsupported_period(provider):
    with pytest.raises(DataFetchError) as exc:
        provider.get_kline_history("000001", "1min", "20260401", "20260402", "qfq")
    assert exc.value.kind == "data"
