from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.akshare.market.realtime import AkshareMarketRealtime
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def mock_legu_df():
    return pd.DataFrame([
        {"item": "上涨", "value": 30.0},
        {"item": "涨停", "value": 5.0},
        {"item": "下跌", "value": 15.0},
        {"item": "跌停", "value": 2.0},
        {"item": "平盘", "value": 5.0},
        {"item": "停牌", "value": 3.0},
        {"item": "统计日期", "value": "2026-03-20 15:00:00"},
    ])


def test_get_market_stats_returns_data_result(mock_legu_df):
    with patch("finance_data.provider.akshare.market.realtime.ak.stock_market_activity_legu",
               return_value=mock_legu_df):
        result = AkshareMarketRealtime().get_market_stats_realtime()
    assert isinstance(result, DataResult)
    assert result.source == "akshare"


def test_get_market_stats_counts(mock_legu_df):
    with patch("finance_data.provider.akshare.market.realtime.ak.stock_market_activity_legu",
               return_value=mock_legu_df):
        result = AkshareMarketRealtime().get_market_stats_realtime()
    row = result.data[0]
    assert row["up_count"] == 30
    assert row["down_count"] == 15
    assert row["flat_count"] == 5
    assert row["total_count"] == 50
    assert row["date"] == "20260320"


def test_get_market_stats_network_error():
    with patch("finance_data.provider.akshare.market.realtime.ak.stock_market_activity_legu",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            AkshareMarketRealtime().get_market_stats_realtime()
    assert exc.value.kind == "network"
