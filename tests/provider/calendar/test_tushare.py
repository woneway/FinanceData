from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from finance_data.provider.calendar.tushare import get_trade_calendar
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_pro():
    return MagicMock()


@pytest.fixture
def mock_cal_df():
    return pd.DataFrame([
        {"cal_date": "20240101", "is_open": 0},
        {"cal_date": "20240102", "is_open": 1},
    ])


def test_get_trade_calendar_returns_data_result(mock_pro, mock_cal_df):
    mock_pro.trade_cal.return_value = mock_cal_df
    with patch("finance_data.provider.calendar.tushare._get_pro", return_value=mock_pro):
        result = get_trade_calendar(start="20240101", end="20240102")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert len(result.data) == 2


def test_get_trade_calendar_fields(mock_pro, mock_cal_df):
    mock_pro.trade_cal.return_value = mock_cal_df
    with patch("finance_data.provider.calendar.tushare._get_pro", return_value=mock_pro):
        result = get_trade_calendar(start="20240101", end="20240102")
    assert result.data[0] == {"date": "20240101", "is_open": False}
    assert result.data[1] == {"date": "20240102", "is_open": True}


def test_get_trade_calendar_empty_raises(mock_pro):
    mock_pro.trade_cal.return_value = pd.DataFrame()
    with patch("finance_data.provider.calendar.tushare._get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            get_trade_calendar(start="20240101", end="20240101")
    assert exc.value.kind == "data"
