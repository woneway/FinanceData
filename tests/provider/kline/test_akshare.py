from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.akshare.kline.history import AkshareKlineHistory
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return AkshareKlineHistory()


@pytest.fixture
def mock_tx_df():
    """腾讯源返回 date/open/close/high/low/amount"""
    return pd.DataFrame([
        {"date": "2023-12-29", "open": 9.8, "close": 10.0, "high": 10.1, "low": 9.7, "amount": 100000.0},
        {"date": "2024-01-01", "open": 10.0, "close": 10.5, "high": 11.0, "low": 9.5, "amount": 1050000.0},
    ])


def test_get_kline_daily_returns_data_result(provider, mock_tx_df):
    with patch("finance_data.provider.akshare.kline.history.ak.stock_zh_a_hist_tx",
               return_value=mock_tx_df):
        result = provider.get_kline_history("000001", period="daily", start="20240101", end="20240101")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1
    assert result.meta["upstream"] == "tencent"


def test_get_kline_daily_fields(provider, mock_tx_df):
    with patch("finance_data.provider.akshare.kline.history.ak.stock_zh_a_hist_tx",
               return_value=mock_tx_df):
        result = provider.get_kline_history("000001", period="daily", start="20240101", end="20240101")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["date"] == "20240101"
    assert row["period"] == "daily"
    assert row["open"] == 10.0
    assert row["close"] == 10.5
    assert row["adj"] == "qfq"


def test_get_kline_network_error(provider):
    with patch("finance_data.provider.akshare.kline.history.ak.stock_zh_a_hist_tx",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            provider.get_kline_history("000001", period="daily", start="20240101", end="20240101")
    assert exc.value.kind == "network"


def test_get_kline_empty_raises_data_error(provider):
    with patch("finance_data.provider.akshare.kline.history.ak.stock_zh_a_hist_tx",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            provider.get_kline_history("000001", period="daily", start="20240101", end="20240101")
    assert exc.value.kind == "data"


def test_unsupported_period_raises(provider):
    """分钟级已下线，应抛出 DataFetchError"""
    with pytest.raises(DataFetchError) as exc:
        provider.get_kline_history("000001", period="1min", start="20240101", end="20240101")
    assert exc.value.kind == "data"


# --- 新独立方法测试 ---

def test_get_daily_kline_history(provider, mock_tx_df):
    with patch("finance_data.provider.akshare.kline.history.ak.stock_zh_a_hist_tx",
               return_value=mock_tx_df):
        result = provider.get_daily_kline_history("000001", start="20240101", end="20240101")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert result.meta["upstream"] == "tencent"
    assert result.data[0]["period"] == "daily"


def test_get_daily_kline_network_error(provider):
    with patch("finance_data.provider.akshare.kline.history.ak.stock_zh_a_hist_tx",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            provider.get_daily_kline_history("000001", start="20240101", end="20240101")
    assert exc.value.kind == "network"
