from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.index.akshare import get_index_quote, get_index_history
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_index_df():
    return pd.DataFrame([{
        "代码": "000001", "名称": "上证指数",
        "最新价": 3100.0, "涨跌幅": 0.5,
        "成交量": 1e10, "成交额": 1e12,
    }])


def test_get_index_quote_returns_data_result(mock_index_df):
    with patch("finance_data.provider.index.akshare.ak.stock_zh_index_spot_sina",
               return_value=mock_index_df):
        result = get_index_quote("000001.SH")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"


def test_get_index_quote_fields(mock_index_df):
    with patch("finance_data.provider.index.akshare.ak.stock_zh_index_spot_sina",
               return_value=mock_index_df):
        result = get_index_quote("000001.SH")
    row = result.data[0]
    assert row["symbol"] == "000001.SH"
    assert row["price"] == 3100.0


@pytest.fixture
def mock_hist_df():
    return pd.DataFrame([{
        "日期": "2024-01-02", "开盘": 3090.0, "最高": 3110.0,
        "最低": 3085.0, "收盘": 3100.0, "成交量": 1e10,
        "成交额": 1e12, "涨跌幅": 0.5,
    }])


def test_get_index_history_returns_data_result(mock_hist_df):
    with patch("finance_data.provider.index.akshare.ak.stock_zh_index_daily_em",
               return_value=mock_hist_df):
        result = get_index_history("000001.SH", start="20240101", end="20240102")
    assert isinstance(result, DataResult)
    assert result.data[0]["close"] == 3100.0


def test_get_index_quote_not_found():
    df = pd.DataFrame([{"代码": "999999", "名称": "X", "最新价": 0.0, "涨跌幅": 0.0, "成交量": 0.0, "成交额": 0.0}])
    with patch("finance_data.provider.index.akshare.ak.stock_zh_index_spot_sina",
               return_value=df):
        with pytest.raises(DataFetchError) as exc:
            get_index_quote("000001.SH")
    assert exc.value.kind == "data"
