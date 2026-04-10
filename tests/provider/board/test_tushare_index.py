from unittest.mock import patch

import pandas as pd
import pytest

from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.board.index import TushareBoardIndex


@pytest.fixture
def provider():
    return TushareBoardIndex()


@pytest.fixture
def mock_df():
    return pd.DataFrame(
        [
            {
                "ts_code": "BK1283.DC",
                "trade_date": "20260410",
                "name": "银行",
                "leading": "沪农商行",
                "leading_code": "601825.SH",
                "pct_change": 0.09,
                "leading_pct": 1.77,
                "total_mv": 1.480165e9,
                "turnover_rate": 0.16,
                "up_num": 18,
                "down_num": 20,
                "idx_type": "行业板块",
                "level": "东财一级行业",
            }
        ]
    )


def test_returns_data_result(provider, mock_df):
    mock_pro = type("MockPro", (), {"dc_index": lambda self, **kwargs: mock_df})()
    with patch("finance_data.provider.tushare.board.index.get_pro", return_value=mock_pro):
        result = provider.get_board_index(idx_type="行业板块")

    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert len(result.data) == 1
    row = result.data[0]
    assert row["board_code"] == "BK1283.DC"
    assert row["board_name"] == "银行"
    assert row["idx_type"] == "行业板块"
    assert row["leading_stock"] == "沪农商行"


def test_empty_raises(provider):
    mock_pro = type("MockPro", (), {"dc_index": lambda self, **kwargs: pd.DataFrame()})()
    with patch("finance_data.provider.tushare.board.index.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            provider.get_board_index(idx_type="行业板块")
    assert exc.value.kind == "data"
