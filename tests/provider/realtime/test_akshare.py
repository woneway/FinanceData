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
    return pd.DataFrame([{
        "代码": "000001", "名称": "平安银行",
        "最新价": 12.5, "涨跌幅": 1.2,
        "成交量": 1000000, "成交额": 12500000.0,
    }])


def test_get_realtime_quote_returns_data_result(provider, mock_spot_df):
    with patch("finance_data.provider.akshare.realtime.realtime.ak.stock_zh_a_spot",
               return_value=mock_spot_df):
        result = provider.get_realtime_quote("000001")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"


def test_get_realtime_quote_fields(provider, mock_spot_df):
    with patch("finance_data.provider.akshare.realtime.realtime.ak.stock_zh_a_spot",
               return_value=mock_spot_df):
        result = provider.get_realtime_quote("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["name"] == "平安银行"
    assert row["price"] == 12.5
    assert row["pct_chg"] == 1.2
    # 新浪源不含市值/PE/PB/换手率
    assert row["market_cap"] is None
    assert row["pe"] is None
    assert row["pb"] is None
    assert row["turnover_rate"] is None


def test_get_realtime_quote_network_error(provider):
    with patch("finance_data.provider.akshare.realtime.realtime.ak.stock_zh_a_spot",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            provider.get_realtime_quote("000001")
    assert exc.value.kind == "network"
