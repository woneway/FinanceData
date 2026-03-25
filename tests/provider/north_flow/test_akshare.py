from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from finance_data.provider.akshare.north_flow.history import AkshareNorthFlow, AkshareNorthStockHold
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


@pytest.fixture
def mock_hold_df():
    return pd.DataFrame([{
        "代码": "600000",
        "名称": "浦发银行",
        "日期": "2024-03-01",
        "今日收盘价": 10.5,
        "今日涨跌幅": 1.2,
        "今日持股-股数": 1e8,
        "今日持股-市值": 1.05e9,
        "今日持股-占流通股比": 2.5,
        "今日持股-占总股本比": 2.3,
        "5日增持估计-股数": 1e6,
        "5日增持估计-市值": 1.05e7,
        "5日增持估计-市值增幅": 0.1,
        "5日增持估计-占流通股比": 0.2,
        "5日增持估计-占总股本比": 0.18,
        "所属板块": "银行",
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


def test_get_north_stock_hold_returns_data(mock_hold_df):
    with patch("finance_data.provider.akshare.north_flow.history.ak.stock_hsgt_hold_stock_em",
               return_value=mock_hold_df):
        result = AkshareNorthStockHold().get_north_stock_hold_history(
            market="沪股通", indicator="5日排行", symbol="", trade_date=""
        )
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1


def test_get_north_stock_hold_fields(mock_hold_df):
    with patch("finance_data.provider.akshare.north_flow.history.ak.stock_hsgt_hold_stock_em",
               return_value=mock_hold_df):
        result = AkshareNorthStockHold().get_north_stock_hold_history(
            market="沪股通", indicator="5日排行", symbol="", trade_date=""
        )
    row = result.data[0]
    assert row["symbol"] == "600000"
    assert row["name"] == "浦发银行"
    assert row["close_price"] == 10.5
    assert row["hold_volume"] == 1e8
    assert row["increase_5d_volume"] == 1e6


def test_get_north_stock_hold_network_error():
    with patch("finance_data.provider.akshare.north_flow.history.ak.stock_hsgt_hold_stock_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            AkshareNorthStockHold().get_north_stock_hold_history(
                market="沪股通", indicator="5日排行", symbol="", trade_date=""
            )
    assert exc.value.kind == "network"


def test_get_north_stock_hold_empty_raises():
    with patch("finance_data.provider.akshare.north_flow.history.ak.stock_hsgt_hold_stock_em",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            AkshareNorthStockHold().get_north_stock_hold_history(
                market="沪股通", indicator="5日排行", symbol="", trade_date=""
            )
    assert exc.value.kind == "data"
