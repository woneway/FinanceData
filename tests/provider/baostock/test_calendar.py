"""baostock 交易日历测试"""
from unittest.mock import patch, MagicMock
import pytest
from finance_data.provider.baostock.calendar.history import BaostockTradeCalendar
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return BaostockTradeCalendar()


def _mock_session(rows):
    from contextlib import contextmanager

    @contextmanager
    def _session():
        bs_mock = MagicMock()
        rs = MagicMock()
        rs.error_code = "0"
        rs._data = list(rows)
        rs._idx = 0

        def _next():
            return rs._idx < len(rs._data)

        def _get_row():
            row = rs._data[rs._idx]
            rs._idx += 1
            return row

        rs.next = _next
        rs.get_row_data = _get_row
        bs_mock.query_trade_dates.return_value = rs
        yield bs_mock

    return _session


def test_returns_data_result(provider):
    rows = [
        ["2026-04-01", "1"],
        ["2026-04-02", "1"],
        ["2026-04-03", "0"],
    ]
    with patch("finance_data.provider.baostock.calendar.history.baostock_session", _mock_session(rows)):
        result = provider.get_trade_calendar_history("20260401", "20260403")
    assert isinstance(result, DataResult)
    assert result.source == "baostock"
    assert len(result.data) == 3
    assert result.data[0]["date"] == "20260401"
    assert result.data[0]["is_open"] is True
    assert result.data[2]["is_open"] is False


def test_empty_raises(provider):
    with patch("finance_data.provider.baostock.calendar.history.baostock_session", _mock_session([])):
        with pytest.raises(DataFetchError) as exc:
            provider.get_trade_calendar_history("20260401", "20260403")
    assert exc.value.kind == "data"


def test_network_error(provider):
    from contextlib import contextmanager

    @contextmanager
    def _error_session():
        raise ConnectionError("baostock server down")
        yield  # noqa: unreachable

    with patch("finance_data.provider.baostock.calendar.history.baostock_session", _error_session):
        with pytest.raises(DataFetchError) as exc:
            provider.get_trade_calendar_history("20260401", "20260403")
    assert exc.value.kind == "network"
