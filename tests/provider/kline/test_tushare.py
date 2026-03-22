from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from finance_data.provider.kline.tushare import get_kline
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_pro():
    return MagicMock()


@pytest.fixture
def mock_daily_df():
    return pd.DataFrame([{
        "trade_date": "20240101", "open": 10.0, "high": 11.0,
        "low": 9.5, "close": 10.5, "vol": 100000.0,
        "amount": 1050000.0, "pct_chg": 1.5,
    }])


def test_get_kline_daily_returns_data_result(mock_pro, mock_daily_df):
    mock_pro.daily.return_value = mock_daily_df
    with patch("finance_data.provider.kline.tushare._get_pro", return_value=mock_pro):
        result = get_kline("000001", period="daily", start="20240101", end="20240101")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"


def test_get_kline_daily_fields(mock_pro, mock_daily_df):
    mock_pro.daily.return_value = mock_daily_df
    with patch("finance_data.provider.kline.tushare._get_pro", return_value=mock_pro):
        result = get_kline("000001", period="daily", start="20240101", end="20240101")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["date"] == "20240101"
    assert row["close"] == 10.5
    assert row["adj"] == "qfq"


def test_get_kline_empty_raises(mock_pro):
    mock_pro.daily.return_value = pd.DataFrame()
    with patch("finance_data.provider.kline.tushare._get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            get_kline("INVALID", period="daily", start="20240101", end="20240101")
    assert exc.value.kind == "data"


def test_get_kline_network_error(mock_pro):
    mock_pro.daily.side_effect = ConnectionError("timeout")
    with patch("finance_data.provider.kline.tushare._get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            get_kline("000001", period="daily", start="20240101", end="20240101")
    assert exc.value.kind == "network"


def test_get_kline_weekly(mock_pro):
    df = pd.DataFrame([{
        "trade_date": "20240101", "open": 10.0, "high": 11.0,
        "low": 9.5, "close": 10.5, "vol": 500000.0, "amount": 5000000.0, "pct_chg": 2.0,
    }])
    mock_pro.weekly.return_value = df
    with patch("finance_data.provider.kline.tushare._get_pro", return_value=mock_pro):
        result = get_kline("000001", period="weekly", start="20240101", end="20240101")
    assert result.data[0]["period"] == "weekly"
