"""龙虎榜机构明细 akshare provider 测试"""
from unittest.mock import patch
import pandas as pd
import pytest

from finance_data.provider.akshare.lhb.inst_detail import AkshareLhbInstDetail
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def lhb_inst_detail_df():
    return pd.DataFrame([{
        "序号": 1,
        "代码": "603067",
        "名称": "振华股份",
        "收盘价": 18.5,
        "涨跌幅": 10.0,
        "买方机构数": 3,
        "卖方机构数": 1,
        "机构买入总额": 5e7,
        "机构卖出总额": 1e7,
        "机构买入净额": 4e7,
        "市场总成交额": 2e9,
        "机构净买额占总成交额比": 2.0,
        "换手率": 15.5,
        "流通市值": 2.77e10,
        "上榜原因": "连续三个交易日内收盘价格涨幅偏离值累计达到20%的证券",
        "上榜日期": "2026-04-08",
    }])


def test_get_lhb_inst_detail_returns_data_result(lhb_inst_detail_df):
    with patch("finance_data.provider.akshare.lhb.inst_detail.ak.stock_lhb_jgmmtj_em",
               return_value=lhb_inst_detail_df):
        result = AkshareLhbInstDetail().get_lhb_inst_detail_history("20260401", "20260408")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1
    row = result.data[0]
    assert row["symbol"] == "603067"
    assert row["name"] == "振华股份"
    assert row["inst_buy_count"] == 3
    assert row["inst_sell_count"] == 1
    assert row["inst_buy_amount"] == 5e7
    assert row["inst_net_buy"] == 4e7
    assert row["date"] == "20260408"


def test_get_lhb_inst_detail_empty_raises():
    with patch("finance_data.provider.akshare.lhb.inst_detail.ak.stock_lhb_jgmmtj_em",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            AkshareLhbInstDetail().get_lhb_inst_detail_history("20260401", "20260408")
    assert exc.value.kind == "data"


def test_get_lhb_inst_detail_network_error():
    with patch("finance_data.provider.akshare.lhb.inst_detail.ak.stock_lhb_jgmmtj_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            AkshareLhbInstDetail().get_lhb_inst_detail_history("20260401", "20260408")
    assert exc.value.kind == "network"
