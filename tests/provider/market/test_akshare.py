from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.market.akshare import get_market_stats
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_spot_df():
    rows = []
    for i in range(30):
        rows.append({"代码": f"{i:06d}", "涨跌幅": 1.5, "成交额": 1e7})
    for i in range(30, 45):
        rows.append({"代码": f"{i:06d}", "涨跌幅": -0.8, "成交额": 8e6})
    for i in range(45, 50):
        rows.append({"代码": f"{i:06d}", "涨跌幅": 0.0, "成交额": 5e6})
    return pd.DataFrame(rows)


def test_get_market_stats_returns_data_result(mock_spot_df):
    with patch("finance_data.provider.market.akshare.ak.stock_zh_a_spot_em",
               return_value=mock_spot_df):
        result = get_market_stats()
    assert isinstance(result, DataResult)
    assert result.source == "akshare"


def test_get_market_stats_counts(mock_spot_df):
    with patch("finance_data.provider.market.akshare.ak.stock_zh_a_spot_em",
               return_value=mock_spot_df):
        result = get_market_stats()
    row = result.data[0]
    assert row["up_count"] == 30
    assert row["down_count"] == 15
    assert row["flat_count"] == 5
    assert row["total_count"] == 50


def test_get_market_stats_network_error():
    with patch("finance_data.provider.market.akshare.ak.stock_zh_a_spot_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_market_stats()
    assert exc.value.kind == "network"
