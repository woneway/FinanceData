from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.akshare.realtime.realtime import AkshareRealtimeQuote
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return AkshareRealtimeQuote()


@pytest.fixture
def mock_spot_df():
    """东方财富源 stock_zh_a_spot_em 返回的 DataFrame"""
    return pd.DataFrame([{
        "代码": "000001", "名称": "平安银行",
        "最新价": 12.5, "涨跌幅": 1.2,
        "成交量": 1000000, "成交额": 12500000.0,
        "总市值": 2.4e11, "市盈率-动态": 8.5,
        "市净率": 0.75, "换手率": 1.3,
    }])


def test_get_realtime_quote_returns_data_result(provider, mock_spot_df):
    with patch("finance_data.provider.akshare.realtime.realtime.ak.stock_zh_a_spot_em",
               return_value=mock_spot_df):
        result = provider.get_realtime_quote("000001")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert result.meta["upstream"] == "eastmoney"


def test_get_realtime_quote_fields(provider, mock_spot_df):
    with patch("finance_data.provider.akshare.realtime.realtime.ak.stock_zh_a_spot_em",
               return_value=mock_spot_df):
        result = provider.get_realtime_quote("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["name"] == "平安银行"
    assert row["price"] == 12.5
    assert row["pct_chg"] == 1.2
    assert row["market_cap"] == 2.4e11
    assert row["pe"] == 8.5
    assert row["pb"] == 0.75
    assert row["turnover_rate"] == 1.3


def test_get_realtime_quote_network_error(provider):
    with patch("finance_data.provider.akshare.realtime.realtime.ak.stock_zh_a_spot_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            provider.get_realtime_quote("000001")
    assert exc.value.kind == "network"
