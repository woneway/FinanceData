from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.kline.akshare import get_kline
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_daily_df():
    return pd.DataFrame([{
        "日期": "2024-01-01", "开盘": 10.0, "最高": 11.0, "最低": 9.5,
        "收盘": 10.5, "成交量": 100000, "成交额": 1050000.0, "涨跌幅": 1.5,
    }])


def test_get_kline_daily_returns_data_result(mock_daily_df):
    with patch("finance_data.provider.kline.akshare.ak.stock_zh_a_hist",
               return_value=mock_daily_df):
        result = get_kline("000001", period="daily", start="20240101", end="20240101")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1


def test_get_kline_daily_fields(mock_daily_df):
    with patch("finance_data.provider.kline.akshare.ak.stock_zh_a_hist",
               return_value=mock_daily_df):
        result = get_kline("000001", period="daily", start="20240101", end="20240101")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["date"] == "20240101"
    assert row["period"] == "daily"
    assert row["open"] == 10.0
    assert row["close"] == 10.5
    assert row["adj"] == "qfq"


def test_get_kline_network_error():
    with patch("finance_data.provider.kline.akshare.ak.stock_zh_a_hist",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_kline("000001", period="daily", start="20240101", end="20240101")
    assert exc.value.kind == "network"


def test_get_kline_empty_raises_data_error():
    with patch("finance_data.provider.kline.akshare.ak.stock_zh_a_hist",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            get_kline("000001", period="daily", start="20240101", end="20240101")
    assert exc.value.kind == "data"


@pytest.fixture
def mock_min_df():
    return pd.DataFrame([{
        "时间": "2024-01-02 09:31:00", "开盘": 10.0, "最高": 10.2,
        "最低": 9.9, "收盘": 10.1, "成交量": 5000, "成交额": 50500.0, "涨跌幅": 0.5,
    }])


def test_get_kline_1min(mock_min_df):
    with patch("finance_data.provider.kline.akshare.ak.stock_zh_a_hist_min_em",
               return_value=mock_min_df):
        result = get_kline("000001", period="1min", start="20240102", end="20240102")
    assert result.data[0]["period"] == "1min"
    assert result.data[0]["date"] == "20240102"
