from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.akshare.sector_fund_flow.history import AkshareSectorCapitalFlow
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def mock_df():
    return pd.DataFrame([{
        "序号": 1,
        "名称": "银行",
        "今日涨跌幅": 2.5,
        "今日主力净流入-净额": 1e9,
        "今日主力净流入-净占比": 15.2,
        "今日超大单净流入-净额": 5e8,
        "今日超大单净流入-净占比": 7.6,
        "今日大单净流入-净额": 3e8,
        "今日大单净流入-净占比": 4.5,
        "今日中单净流入-净额": -1e8,
        "今日中单净流入-净占比": -1.5,
        "今日小单净流入-净额": -7e8,
        "今日小单净流入-净占比": -10.6,
        "今日主力净流入最大股": "工商银行",
    }])


def test_get_sector_capital_flow_returns_data_result(mock_df):
    with patch("finance_data.provider.akshare.sector_fund_flow.history.ak.stock_sector_fund_flow_rank",
               return_value=mock_df):
        result = AkshareSectorCapitalFlow().get_sector_capital_flow_history(
            indicator="今日", sector_type="行业资金流"
        )
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1


def test_get_sector_capital_flow_fields(mock_df):
    with patch("finance_data.provider.akshare.sector_fund_flow.history.ak.stock_sector_fund_flow_rank",
               return_value=mock_df):
        result = AkshareSectorCapitalFlow().get_sector_capital_flow_history(
            indicator="今日", sector_type="行业资金流"
        )
    row = result.data[0]
    assert row["rank"] == 1
    assert row["name"] == "银行"
    assert row["pct_chg"] == 2.5
    assert row["main_net_inflow"] == 1e9
    assert row["main_net_inflow_pct"] == 15.2
    assert row["top_stock"] == "工商银行"


def test_get_sector_capital_flow_network_error():
    with patch("finance_data.provider.akshare.sector_fund_flow.history.ak.stock_sector_fund_flow_rank",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            AkshareSectorCapitalFlow().get_sector_capital_flow_history(
                indicator="今日", sector_type="行业资金流"
            )
    assert exc.value.kind == "network"


def test_get_sector_capital_flow_empty_raises():
    with patch("finance_data.provider.akshare.sector_fund_flow.history.ak.stock_sector_fund_flow_rank",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            AkshareSectorCapitalFlow().get_sector_capital_flow_history(
                indicator="今日", sector_type="行业资金流"
            )
    assert exc.value.kind == "data"


def test_get_sector_capital_flow_3day_indicator(mock_df):
    df_3day = mock_df.copy()
    df_3day.columns = [c.replace("今日", "3日") for c in df_3day.columns]
    with patch("finance_data.provider.akshare.sector_fund_flow.history.ak.stock_sector_fund_flow_rank",
               return_value=df_3day):
        result = AkshareSectorCapitalFlow().get_sector_capital_flow_history(
            indicator="3日", sector_type="概念资金流"
        )
    assert result.data[0]["pct_chg"] == 2.5


def test_get_sector_capital_flow_concept_type(mock_df):
    with patch("finance_data.provider.akshare.sector_fund_flow.history.ak.stock_sector_fund_flow_rank",
               return_value=mock_df):
        result = AkshareSectorCapitalFlow().get_sector_capital_flow_history(
            indicator="今日", sector_type="概念资金流"
        )
    assert result.meta["indicator"] == "今日"
    assert result.meta["sector_type"] == "概念资金流"
