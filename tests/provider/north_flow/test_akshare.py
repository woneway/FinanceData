from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.akshare.north_flow.history import AkshareNorthFlow
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def mock_flow_df():
    return pd.DataFrame([{
        "交易日": "2024-03-01",
        "类型": "沪港通",
        "板块": "沪股通",
        "资金方向": "北向",
        "交易状态": 3,
        "成交净买额": 1.5e9,
        "资金净流入": 1.4e9,
        "当日资金余额": 1.0e12,
        "上涨数": 100,
        "持平数": 50,
        "下跌数": 30,
        "相关指数": "上证指数",
        "指数涨跌幅": 0.5,
    }])


def test_get_north_flow_returns_data_result(mock_flow_df):
    with patch("finance_data.provider.akshare.north_flow.history.ak.stock_hsgt_fund_flow_summary_em",
               return_value=mock_flow_df):
        result = AkshareNorthFlow().get_north_flow_history()
    assert isinstance(result, DataResult)
    assert result.source == "akshare"


def test_get_north_flow_fields(mock_flow_df):
    with patch("finance_data.provider.akshare.north_flow.history.ak.stock_hsgt_fund_flow_summary_em",
               return_value=mock_flow_df):
        result = AkshareNorthFlow().get_north_flow_history()
    row = result.data[0]
    assert row["date"] == "20240301"
    assert row["market"] == "沪股通"
    assert row["direction"] == "北向"
    assert row["net_buy"] == 1.5e9
    assert row["net_inflow"] == 1.4e9


def test_get_north_flow_skips_south(mock_flow_df):
    south_df = mock_flow_df.copy()
    south_df["资金方向"] = "南向"
    with patch("finance_data.provider.akshare.north_flow.history.ak.stock_hsgt_fund_flow_summary_em",
               return_value=pd.concat([mock_flow_df, south_df])):
        result = AkshareNorthFlow().get_north_flow_history()
    assert all(r["direction"] == "北向" for r in result.data)


def test_get_north_flow_network_error():
    with patch("finance_data.provider.akshare.north_flow.history.ak.stock_hsgt_fund_flow_summary_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            AkshareNorthFlow().get_north_flow_history()
    assert exc.value.kind == "network"


def test_get_north_flow_empty_raises():
    with patch("finance_data.provider.akshare.north_flow.history.ak.stock_hsgt_fund_flow_summary_em",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            AkshareNorthFlow().get_north_flow_history()
    assert exc.value.kind == "data"
