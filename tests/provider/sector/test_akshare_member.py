from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.akshare.sector.member import AkshareSectorMember
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return AkshareSectorMember()


@pytest.fixture
def mock_df():
    return pd.DataFrame([{
        "序号": 1,
        "代码": "601398",
        "名称": "工商银行",
        "最新价": 5.68,
        "涨跌幅": 1.25,
        "涨跌额": 0.07,
        "成交量": 50000000,
        "成交额": 284000000,
        "振幅": 1.78,
        "最高": 5.72,
        "最低": 5.62,
        "今开": 5.63,
        "昨收": 5.61,
        "换手率": 0.14,
        "市盈率-动态": 5.12,
        "市净率": 0.65,
    }])


def test_returns_data_result(provider, mock_df):
    with patch(
        "finance_data.provider.akshare.sector.member.ak.stock_board_industry_cons_em",
        return_value=mock_df,
    ):
        result = provider.get_sector_member(symbol="银行")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1
    row = result.data[0]
    assert row["symbol"] == "601398"
    assert row["name"] == "工商银行"
    assert row["price"] == 5.68
    assert row["pct_chg"] == 1.25
    assert row["volume"] == 50000000
    assert row["pe_ratio"] == 5.12
    assert row["pb_ratio"] == 0.65


def test_empty_raises(provider):
    with patch(
        "finance_data.provider.akshare.sector.member.ak.stock_board_industry_cons_em",
        return_value=pd.DataFrame(),
    ):
        with pytest.raises(DataFetchError) as exc:
            provider.get_sector_member(symbol="银行")
    assert exc.value.kind == "data"


def test_network_error(provider):
    with patch(
        "finance_data.provider.akshare.sector.member.ak.stock_board_industry_cons_em",
        side_effect=TimeoutError("timeout"),
    ):
        with pytest.raises(DataFetchError) as exc:
            provider.get_sector_member(symbol="银行")
    assert exc.value.kind == "network"
