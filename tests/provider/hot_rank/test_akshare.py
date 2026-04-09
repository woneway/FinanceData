"""热股排行 akshare provider 测试"""
from unittest.mock import patch
import pandas as pd
import pytest

from finance_data.provider.akshare.hot_rank.realtime import AkshareHotRank
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def hot_rank_df():
    return pd.DataFrame([{
        "当前排名": 1,
        "代码": "SZ300058",
        "股票名称": "蓝色光标",
        "最新价": 16.34,
        "涨跌额": 0.029412,
        "涨跌幅": 0.18,
    }])


def test_get_hot_rank_returns_data_result(hot_rank_df):
    with patch("finance_data.provider.akshare.hot_rank.realtime.ak.stock_hot_rank_em",
               return_value=hot_rank_df):
        result = AkshareHotRank().get_hot_rank_realtime()
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1
    row = result.data[0]
    assert row["rank"] == 1
    assert row["symbol"] == "300058"
    assert row["name"] == "蓝色光标"
    assert row["latest_price"] == 16.34
    assert row["pct_change"] == 0.18


def test_get_hot_rank_empty_raises():
    with patch("finance_data.provider.akshare.hot_rank.realtime.ak.stock_hot_rank_em",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            AkshareHotRank().get_hot_rank_realtime()
    assert exc.value.kind == "data"


def test_get_hot_rank_network_error():
    with patch("finance_data.provider.akshare.hot_rank.realtime.ak.stock_hot_rank_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            AkshareHotRank().get_hot_rank_realtime()
    assert exc.value.kind == "network"
