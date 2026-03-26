from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.akshare.index.realtime import AkshareIndexQuote
from finance_data.provider.akshare.index.history import AkshareIndexHistory
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def quote_provider():
    return AkshareIndexQuote()


@pytest.fixture
def history_provider():
    return AkshareIndexHistory()


@pytest.fixture
def mock_index_df():
    # sina 格式代码带交易所前缀，如 sh000001
    return pd.DataFrame([{
        "代码": "sh000001", "名称": "上证指数",
        "最新价": 3100.0, "涨跌幅": 0.5,
        "成交量": 1e10, "成交额": 1e12,
    }])


def test_get_index_quote_returns_data_result(quote_provider, mock_index_df):
    with patch("finance_data.provider.akshare.index.realtime.ak.stock_zh_index_spot_sina",
               return_value=mock_index_df):
        result = quote_provider.get_index_quote_realtime("000001.SH")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"


def test_get_index_quote_fields(quote_provider, mock_index_df):
    with patch("finance_data.provider.akshare.index.realtime.ak.stock_zh_index_spot_sina",
               return_value=mock_index_df):
        result = quote_provider.get_index_quote_realtime("000001.SH")
    row = result.data[0]
    assert row["symbol"] == "000001.SH"
    assert row["price"] == 3100.0


@pytest.fixture
def mock_em_index_df():
    """东方财富源返回 date/open/close/high/low/volume/amount"""
    return pd.DataFrame([
        {"date": "2023-12-29", "open": 3050.0, "close": 3080.0, "high": 3090.0, "low": 3040.0, "volume": 5e9, "amount": 5e11},
        {"date": "2024-01-02", "open": 3090.0, "close": 3100.0, "high": 3110.0, "low": 3085.0, "volume": 6e9, "amount": 1e12},
    ])


def test_get_index_history_returns_data_result(history_provider, mock_em_index_df):
    with patch("finance_data.provider.akshare.index.history.ak.stock_zh_index_daily_em",
               return_value=mock_em_index_df):
        result = history_provider.get_index_history("000001.SH", start="20240101", end="20240102")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert result.data[0]["close"] == 3100.0
    assert result.meta["upstream"] == "eastmoney"


def test_get_index_history_has_amount(history_provider, mock_em_index_df):
    with patch("finance_data.provider.akshare.index.history.ak.stock_zh_index_daily_em",
               return_value=mock_em_index_df):
        result = history_provider.get_index_history("000001.SH", start="20240101", end="20240102")
    bar = result.data[0]
    assert bar["amount"] == 1e12
    assert bar["volume"] == 6e9


def test_get_index_history_pct_chg_calculated(history_provider, mock_em_index_df):
    with patch("finance_data.provider.akshare.index.history.ak.stock_zh_index_daily_em",
               return_value=mock_em_index_df):
        result = history_provider.get_index_history("000001.SH", start="20240101", end="20240102")
    bar = result.data[0]
    # pct_chg = (3100 - 3080) / 3080 * 100 ≈ 0.65
    assert bar["pct_chg"] == pytest.approx(0.65, abs=0.01)


def test_get_index_quote_not_found(quote_provider):
    df = pd.DataFrame([{"代码": "999999", "名称": "X", "最新价": 0.0, "涨跌幅": 0.0, "成交量": 0.0, "成交额": 0.0}])
    with patch("finance_data.provider.akshare.index.realtime.ak.stock_zh_index_spot_sina",
               return_value=df):
        with pytest.raises(DataFetchError) as exc:
            quote_provider.get_index_quote_realtime("000001.SH")
    assert exc.value.kind == "data"
