from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.akshare.sector.realtime import AkshareSectorRank
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return AkshareSectorRank()


@pytest.fixture
def mock_sector_df():
    return pd.DataFrame([{
        "板块": "银行", "涨跌幅": 1.2,
        "领涨股": "招商银行", "领涨股-涨跌幅": 3.5,
        "上涨家数": 35, "下跌家数": 5,
    }])


def test_get_sector_rank_returns_data_result(provider, mock_sector_df):
    with patch("finance_data.provider.akshare.sector.realtime.ak.stock_board_industry_summary_ths",
               return_value=mock_sector_df):
        result = provider.get_sector_rank_realtime()
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1


def test_get_sector_rank_fields(provider, mock_sector_df):
    with patch("finance_data.provider.akshare.sector.realtime.ak.stock_board_industry_summary_ths",
               return_value=mock_sector_df):
        result = provider.get_sector_rank_realtime()
    row = result.data[0]
    assert row["name"] == "银行"
    assert row["pct_chg"] == 1.2
    assert row["leader_stock"] == "招商银行"


def test_get_sector_rank_network_error(provider):
    with patch("finance_data.provider.akshare.sector.realtime.ak.stock_board_industry_summary_ths",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            provider.get_sector_rank_realtime()
    assert exc.value.kind == "network"
