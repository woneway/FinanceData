from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.cashflow.akshare import get_fund_flow
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_flow_df():
    return pd.DataFrame([{
        "日期": "2024-01-02",
        "主力净流入-净额": 1.2e8, "主力净流入-净占比": 2.3,
        "超大单净流入-净额": 5.0e7, "超大单净流入-净占比": 1.1,
    }])


def test_get_fund_flow_returns_data_result(mock_flow_df):
    with patch("finance_data.provider.cashflow.akshare.ak.stock_individual_fund_flow",
               return_value=mock_flow_df):
        result = get_fund_flow("000001")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"


def test_get_fund_flow_fields(mock_flow_df):
    with patch("finance_data.provider.cashflow.akshare.ak.stock_individual_fund_flow",
               return_value=mock_flow_df):
        result = get_fund_flow("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["net_inflow"] == 1.2e8
    assert row["main_net_inflow"] == 1.2e8
    assert row["super_large_net_inflow"] == 5.0e7
    assert row["super_large_net_inflow_pct"] == 1.1


def test_get_fund_flow_network_error():
    with patch("finance_data.provider.cashflow.akshare.ak.stock_individual_fund_flow",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_fund_flow("000001")
    assert exc.value.kind == "network"


def test_get_fund_flow_empty_raises():
    with patch("finance_data.provider.cashflow.akshare.ak.stock_individual_fund_flow",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            get_fund_flow("INVALID")
    assert exc.value.kind == "data"
