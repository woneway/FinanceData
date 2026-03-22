from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.sector.akshare import get_sector_rank
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_sector_df():
    return pd.DataFrame([{
        "板块名称": "银行", "涨跌幅": 1.2,
        "领涨股票": "招商银行", "领涨股票-涨跌幅": 3.5,
        "上涨家数": 35, "下跌家数": 5,
    }])


def test_get_sector_rank_returns_data_result(mock_sector_df):
    with patch("finance_data.provider.sector.akshare.ak.stock_board_industry_name_em",
               return_value=mock_sector_df):
        result = get_sector_rank()
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1


def test_get_sector_rank_fields(mock_sector_df):
    with patch("finance_data.provider.sector.akshare.ak.stock_board_industry_name_em",
               return_value=mock_sector_df):
        result = get_sector_rank()
    row = result.data[0]
    assert row["name"] == "银行"
    assert row["pct_chg"] == 1.2
    assert row["leader_stock"] == "招商银行"


def test_get_sector_rank_network_error():
    with patch("finance_data.provider.sector.akshare.ak.stock_board_industry_name_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_sector_rank()
    assert exc.value.kind == "network"
