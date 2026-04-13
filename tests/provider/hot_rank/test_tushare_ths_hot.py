from unittest.mock import patch

import pandas as pd
import pytest

from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.hot_rank.ths_hot import TushareThsHot


@pytest.fixture
def provider():
    return TushareThsHot()


@pytest.fixture
def mock_df():
    return pd.DataFrame(
        [
            {
                "trade_date": "20260410",
                "data_type": "热股",
                "ts_code": "600105.SH",
                "ts_name": "永鼎股份",
                "rank": 1,
                "pct_change": 9.99,
                "current_price": 38.10,
                "hot": 604924.0,
                "concept": '["共封装光学(CPO)"]',
                "rank_time": "2026-04-10 22:30:00",
                "rank_reason": "AI算力需求",
            },
            {
                "trade_date": "20260410",
                "data_type": "热股",
                "ts_code": "600105.SH",
                "ts_name": "永鼎股份",
                "rank": 1,
                "pct_change": 9.99,
                "current_price": 38.10,
                "hot": 578442.0,
                "concept": '["共封装光学(CPO)"]',
                "rank_time": "2026-04-10 21:30:00",
                "rank_reason": "AI算力需求",
            },
            {
                "trade_date": "20260410",
                "data_type": "ETF",
                "ts_code": "159915.SZ",
                "ts_name": "创业板ETF",
                "rank": 1,
                "pct_change": 2.5,
                "current_price": 3.0,
                "hot": 100.0,
                "concept": None,
                "rank_time": "2026-04-10 22:30:00",
                "rank_reason": None,
            },
        ]
    )


def test_returns_data_result_with_dedup(provider, mock_df):
    mock_pro = type("MockPro", (), {"ths_hot": lambda self, **kw: mock_df})()
    with patch("finance_data.provider.tushare.hot_rank.ths_hot.get_pro", return_value=mock_pro):
        result = provider.get_ths_hot()

    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert len(result.data) == 1
    row = result.data[0]
    assert row["symbol"] == "600105.SH"
    assert row["rank"] == 1
    assert row["pct_chg"] == 9.99
    assert row["hot"] == 604924.0


def test_empty_raises(provider):
    mock_pro = type("MockPro", (), {"ths_hot": lambda self, **kw: pd.DataFrame()})()
    with patch("finance_data.provider.tushare.hot_rank.ths_hot.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            provider.get_ths_hot()
    assert exc.value.kind == "data"
