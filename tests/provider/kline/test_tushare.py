from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from finance_data.provider.tushare.kline.history import TushareKlineHistory
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return TushareKlineHistory()


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


def test_get_kline_daily_returns_data_result(provider, mock_pro, mock_daily_df):
    mock_pro.daily.return_value = mock_daily_df
    with patch("finance_data.provider.tushare.kline.history.get_pro", return_value=mock_pro):
        result = provider.get_kline_history("000001", period="daily", start="20240101", end="20240101")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"


def test_get_kline_daily_fields(provider, mock_pro, mock_daily_df):
    mock_pro.daily.return_value = mock_daily_df
    with patch("finance_data.provider.tushare.kline.history.get_pro", return_value=mock_pro):
        result = provider.get_kline_history("000001", period="daily", start="20240101", end="20240101")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["date"] == "20240101"
    assert row["close"] == 10.5
    assert row["adj"] == "qfq"


def test_get_kline_empty_raises(provider, mock_pro):
    mock_pro.daily.return_value = pd.DataFrame()
    with patch("finance_data.provider.tushare.kline.history.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            provider.get_kline_history("INVALID", period="daily", start="20240101", end="20240101")
    assert exc.value.kind == "data"


def test_get_kline_network_error(provider, mock_pro):
    mock_pro.daily.side_effect = ConnectionError("timeout")
    with patch("finance_data.provider.tushare.kline.history.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            provider.get_kline_history("000001", period="daily", start="20240101", end="20240101")
    assert exc.value.kind == "network"


def test_get_kline_weekly(provider, mock_pro):
    df = pd.DataFrame([{
        "trade_date": "20240101", "open": 10.0, "high": 11.0,
        "low": 9.5, "close": 10.5, "vol": 500000.0, "amount": 5000000.0, "pct_chg": 2.0,
    }])
    mock_pro.weekly.return_value = df
    with patch("finance_data.provider.tushare.kline.history.get_pro", return_value=mock_pro):
        result = provider.get_kline_history("000001", period="weekly", start="20240101", end="20240101")
    assert result.data[0]["period"] == "weekly"


# --- 新独立方法测试 ---

def test_get_daily_kline_history(provider, mock_pro, mock_daily_df):
    mock_pro.daily.return_value = mock_daily_df
    with patch("finance_data.provider.tushare.kline.history.get_pro", return_value=mock_pro):
        result = provider.get_daily_kline_history("000001", start="20240101", end="20240101")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert result.data[0]["period"] == "daily"
    assert result.data[0]["volume"] == 10000000.0  # 100000手 × 100


def test_get_weekly_kline_history(provider, mock_pro):
    df = pd.DataFrame([{
        "trade_date": "20240101", "open": 10.0, "high": 11.0,
        "low": 9.5, "close": 10.5, "vol": 500000.0, "amount": 5000000.0, "pct_chg": 0.02,
    }])
    mock_pro.weekly.return_value = df
    with patch("finance_data.provider.tushare.kline.history.get_pro", return_value=mock_pro):
        result = provider.get_weekly_kline_history("000001", start="20240101", end="20240101")
    assert isinstance(result, DataResult)
    assert result.data[0]["period"] == "weekly"
    assert result.data[0]["volume"] == 500000.0
    assert result.data[0]["amount"] == 5000000.0
    assert result.data[0]["pct_chg"] == 2.0


def test_get_monthly_kline_history(provider, mock_pro):
    df = pd.DataFrame([{
        "trade_date": "20240101", "open": 10.0, "high": 11.0,
        "low": 9.5, "close": 10.5, "vol": 500000.0, "amount": 5000000.0, "pct_chg": 0.02,
    }])
    mock_pro.monthly.return_value = df
    with patch("finance_data.provider.tushare.kline.history.get_pro", return_value=mock_pro):
        result = provider.get_monthly_kline_history("000001", start="20240101", end="20240101")
    assert isinstance(result, DataResult)
    assert result.data[0]["period"] == "monthly"
    assert result.data[0]["volume"] == 500000.0
    assert result.data[0]["amount"] == 5000000.0
    assert result.data[0]["pct_chg"] == 2.0


def test_get_daily_kline_empty_raises(provider, mock_pro):
    mock_pro.daily.return_value = pd.DataFrame()
    with patch("finance_data.provider.tushare.kline.history.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            provider.get_daily_kline_history("INVALID", start="20240101", end="20240101")
    assert exc.value.kind == "data"
