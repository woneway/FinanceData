from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.akshare.sector.list import AkshareSectorList
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return AkshareSectorList()


@pytest.fixture
def mock_df():
    return pd.DataFrame([{
        "排名": 1,
        "板块名称": "银行",
        "板块代码": "BK0475",
        "最新价": 1234.56,
        "涨跌额": 12.34,
        "涨跌幅": 1.01,
        "总市值": 1.5e12,
        "换手率": 0.35,
        "上涨家数": 35,
        "下跌家数": 5,
        "领涨股票": "招商银行",
        "领涨股票-涨跌幅": 3.5,
    }])


def test_returns_data_result(provider, mock_df):
    with patch(
        "finance_data.provider.akshare.sector.list.ak.stock_board_industry_name_em",
        return_value=mock_df,
    ):
        result = provider.get_sector_list()
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1
    row = result.data[0]
    assert row["name"] == "银行"
    assert row["code"] == "BK0475"
    assert row["price"] == 1234.56
    assert row["pct_chg"] == 1.01
    assert row["market_cap"] == 1.5e12
    assert row["up_count"] == 35
    assert row["leader_stock"] == "招商银行"


def test_empty_raises(provider):
    with patch(
        "finance_data.provider.akshare.sector.list.ak.stock_board_industry_name_em",
        return_value=pd.DataFrame(),
    ):
        with pytest.raises(DataFetchError) as exc:
            provider.get_sector_list()
    assert exc.value.kind == "data"


def test_network_error(provider):
    with patch(
        "finance_data.provider.akshare.sector.list.ak.stock_board_industry_name_em",
        side_effect=ConnectionError("timeout"),
    ):
        with pytest.raises(DataFetchError) as exc:
            provider.get_sector_list()
    assert exc.value.kind == "network"
