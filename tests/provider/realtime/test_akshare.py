from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.realtime.akshare import get_realtime_quote
from finance_data.provider.realtime import cache
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture(autouse=True)
def clear_cache():
    cache._quote_cache.clear()
    yield
    cache._quote_cache.clear()


@pytest.fixture
def mock_spot_df():
    return pd.DataFrame([{
        "代码": "000001", "名称": "平安银行",
        "最新价": 12.5, "涨跌幅": 1.2,
        "成交量": 1000000, "成交额": 12500000.0,
        "总市值": 2420000000000.0, "市盈率-动态": 6.5, "市净率": 0.8,
        "换手率": 0.52,
    }])


def test_get_realtime_quote_returns_data_result(mock_spot_df):
    with patch("finance_data.provider.realtime.akshare.ak.stock_zh_a_spot_em",
               return_value=mock_spot_df):
        result = get_realtime_quote("000001")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"


def test_get_realtime_quote_fields(mock_spot_df):
    with patch("finance_data.provider.realtime.akshare.ak.stock_zh_a_spot_em",
               return_value=mock_spot_df):
        result = get_realtime_quote("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["name"] == "平安银行"
    assert row["price"] == 12.5
    assert row["pct_chg"] == 1.2


def test_get_realtime_quote_cache_hit(mock_spot_df):
    call_count = 0

    def mock_spot(*a, **kw):
        nonlocal call_count
        call_count += 1
        return mock_spot_df

    with patch("finance_data.provider.realtime.akshare.ak.stock_zh_a_spot_em",
               side_effect=mock_spot):
        get_realtime_quote("000001")
        get_realtime_quote("000001")  # 命中缓存
    assert call_count == 1  # akshare 只被调用一次


def test_get_realtime_quote_network_error():
    with patch("finance_data.provider.realtime.akshare.ak.stock_zh_a_spot_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_realtime_quote("000001")
    assert exc.value.kind == "network"
