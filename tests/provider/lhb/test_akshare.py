"""龙虎榜 akshare provider 测试"""
import math
from unittest.mock import patch
import pandas as pd
import pytest

from finance_data.provider.akshare.lhb.history import (
    AkshareLhbDetail,
    AkshareLhbStockStat,
    AkshareLhbActiveTraders,
    AkshareLhbTraderStat,
    AkshareLhbStockDetail,
)
from finance_data.interface.types import DataResult, DataFetchError


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def lhb_detail_df():
    return pd.DataFrame([{
        "序号": 1, "代码": "000001", "名称": "平安银行",
        "上榜日": "2024-03-20", "解读": "",
        "收盘价": 10.5, "涨跌幅": 5.2,
        "龙虎榜净买额": 1_000_000, "龙虎榜买入额": 5_000_000,
        "龙虎榜卖出额": 4_000_000, "龙虎榜成交额": 9_000_000,
        "市场总成交额": 100_000_000,
        "净买额占总成交比": 1.0, "成交额占总成交比": 9.0,
        "换手率": 2.5, "流通市值": 5e10,
        "上榜原因": "日涨幅偏离值达到7%的前5只证券",
        "上榜后1日": 1.2, "上榜后2日": 0.5, "上榜后5日": -0.3, "上榜后10日": 2.1,
    }])


@pytest.fixture
def lhb_stock_stat_sina_df():
    """新浪源 stock_lhb_ggtj_sina 返回格式"""
    return pd.DataFrame([{
        "股票代码": "000001",
        "股票名称": "平安银行",
        "上榜次数": 3,
        "累积购买额": 8e6,
        "累积卖出额": 6e6,
        "净额": 2e6,
        "买入席位数": 2,
        "卖出席位数": 1,
    }])


@pytest.fixture
def lhb_active_trader_sina_df():
    """新浪源 stock_lhb_yytj_sina 返回格式"""
    return pd.DataFrame([{
        "营业部名称": "华宝证券上海东大名路营业部",
        "上榜次数": 5,
        "累积购买额": 1e7,
        "买入席位数": 5,
        "累积卖出额": 6e6,
        "卖出席位数": 3,
        "买入前三股票": "平安银行,招商银行,贵州茅台,",
    }])


@pytest.fixture
def lhb_active_trader_nan_stocks_df():
    """买入前三股票字段为 NaN"""
    return pd.DataFrame([{
        "营业部名称": "某卖出营业部",
        "上榜次数": 0,
        "累积购买额": 0.0,
        "买入席位数": 0,
        "累积卖出额": 3e6,
        "卖出席位数": 2,
        "买入前三股票": float("nan"),
    }])


@pytest.fixture
def lhb_trader_stat_sina_df():
    """新浪源 stock_lhb_yytj_sina 返回格式（同 active_traders）"""
    return pd.DataFrame([{
        "营业部名称": "华宝证券上海东大名路营业部",
        "上榜次数": 46,
        "累积购买额": 1.2e8,
        "买入席位数": 46,
        "累积卖出额": 8e7,
        "卖出席位数": 42,
        "买入前三股票": "",
    }])


@pytest.fixture
def lhb_stock_detail_sina_df():
    """新浪源 stock_lhb_detail_daily_sina 返回格式"""
    return pd.DataFrame([{
        "序号": 1,
        "股票代码": "000001",
        "股票名称": "平安银行",
        "收盘价": 10.5,
        "对应值": 7.2,
        "成交量": 13890.0,
        "成交额": 5e6,
        "指标": "日涨幅偏离值达7%的证券",
    }])


# ── get_lhb_detail (仍使用东财 mock，AkshareLhbDetail 未改) ─────────────────

def test_get_lhb_detail_returns_data_result(lhb_detail_df):
    with patch("finance_data.provider.akshare.lhb.history.ak.stock_lhb_detail_em",
               return_value=lhb_detail_df):
        result = AkshareLhbDetail().get_lhb_detail_history("20240320", "20240320")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["date"] == "20240320"
    assert row["lhb_net_buy"] == 1_000_000


def test_get_lhb_detail_empty_raises():
    with patch("finance_data.provider.akshare.lhb.history.ak.stock_lhb_detail_em",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            AkshareLhbDetail().get_lhb_detail_history("20240101", "20240101")
    assert exc.value.kind == "data"


def test_get_lhb_detail_network_error():
    with patch("finance_data.provider.akshare.lhb.history.ak.stock_lhb_detail_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            AkshareLhbDetail().get_lhb_detail_history("20240320", "20240320")
    assert exc.value.kind == "network"


# ── get_lhb_stock_stat (新浪源) ──────────────────────────────────────────────

def test_get_lhb_stock_stat_returns_data_result(lhb_stock_stat_sina_df):
    with patch("finance_data.provider.akshare.lhb.history.ak.stock_lhb_ggtj_sina",
               return_value=lhb_stock_stat_sina_df):
        result = AkshareLhbStockStat().get_lhb_stock_stat_history("近一月")
    assert isinstance(result, DataResult)
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["times"] == 3
    assert row["lhb_buy"] == 8e6
    assert row["lhb_sell"] == 6e6
    assert row["lhb_net_buy"] == 2e6
    assert row["inst_buy_times"] == 2
    assert row["inst_sell_times"] == 1


def test_get_lhb_stock_stat_empty_raises():
    with patch("finance_data.provider.akshare.lhb.history.ak.stock_lhb_ggtj_sina",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError):
            AkshareLhbStockStat().get_lhb_stock_stat_history("近一月")


def test_get_lhb_stock_stat_network_error():
    with patch("finance_data.provider.akshare.lhb.history.ak.stock_lhb_ggtj_sina",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            AkshareLhbStockStat().get_lhb_stock_stat_history("近一月")
    assert exc.value.kind == "network"


# ── get_lhb_active_traders (新浪源) ──────────────────────────────────────────

def test_get_lhb_active_traders_returns_data_result(lhb_active_trader_sina_df):
    with patch("finance_data.provider.akshare.lhb.history.ak.stock_lhb_yytj_sina",
               return_value=lhb_active_trader_sina_df):
        result = AkshareLhbActiveTraders().get_lhb_active_traders_history("20240320", "20240320")
    assert isinstance(result, DataResult)
    row = result.data[0]
    assert row["branch_name"] == "华宝证券上海东大名路营业部"
    assert row["buy_count"] == 5
    assert row["buy_amount"] == 1e7
    assert row["sell_amount"] == 6e6
    assert row["net_amount"] == 1e7 - 6e6
    assert "平安银行" in row["stocks"]


def test_get_lhb_active_traders_nan_stocks(lhb_active_trader_nan_stocks_df):
    """NaN 买入前三股票字段应返回空字符串，而不是 'nan'。"""
    with patch("finance_data.provider.akshare.lhb.history.ak.stock_lhb_yytj_sina",
               return_value=lhb_active_trader_nan_stocks_df):
        result = AkshareLhbActiveTraders().get_lhb_active_traders_history("20240320", "20240320")
    assert result.data[0]["stocks"] == ""


def test_get_lhb_active_traders_empty_raises():
    with patch("finance_data.provider.akshare.lhb.history.ak.stock_lhb_yytj_sina",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError):
            AkshareLhbActiveTraders().get_lhb_active_traders_history("20240320", "20240320")


# ── get_lhb_trader_stat (新浪源) ─────────────────────────────────────────────

def test_get_lhb_trader_stat_returns_data_result(lhb_trader_stat_sina_df):
    with patch("finance_data.provider.akshare.lhb.history.ak.stock_lhb_yytj_sina",
               return_value=lhb_trader_stat_sina_df):
        result = AkshareLhbTraderStat().get_lhb_trader_stat_history("近一月")
    assert isinstance(result, DataResult)
    row = result.data[0]
    assert row["branch_name"] == "华宝证券上海东大名路营业部"
    assert row["times"] == 46
    assert row["buy_amount"] == 1.2e8
    assert row["buy_times"] == 46
    assert row["sell_amount"] == 8e7
    assert row["sell_times"] == 42


def test_get_lhb_trader_stat_empty_raises():
    with patch("finance_data.provider.akshare.lhb.history.ak.stock_lhb_yytj_sina",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError):
            AkshareLhbTraderStat().get_lhb_trader_stat_history("近一月")


# ── get_lhb_stock_detail (新浪源) ────────────────────────────────────────────

def test_get_lhb_stock_detail_returns_data(lhb_stock_detail_sina_df):
    with patch("finance_data.provider.akshare.lhb.history.ak.stock_lhb_detail_daily_sina",
               return_value=lhb_stock_detail_sina_df):
        result = AkshareLhbStockDetail().get_lhb_stock_detail_history("000001", "20240320", "买入")
    assert isinstance(result, DataResult)
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["date"] == "20240320"
    assert row["trade_amount"] == 5e6
    assert row["seat_type"] == "日涨幅偏离值达7%的证券"
    assert row["flag"] == "全部"  # 新浪源不区分买入/卖出


def test_get_lhb_stock_detail_empty_raises():
    with patch("finance_data.provider.akshare.lhb.history.ak.stock_lhb_detail_daily_sina",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError):
            AkshareLhbStockDetail().get_lhb_stock_detail_history("000001", "20240320", "买入")


# ── helper edge cases ──────────────────────────────────────────────────────────

def test_int_helper_handles_inf():
    """_int 对 inf 应返回默认值而不是抛出 OverflowError。"""
    from finance_data.provider.akshare.lhb.history import _int
    assert _int(float("inf")) == 0
    assert _int(float("-inf")) == 0
    assert _int(float("nan")) == 0


def test_date_helper_handles_none():
    from finance_data.provider.akshare.lhb.history import _date
    assert _date(None) == ""
    assert _date("2024-03-20") == "20240320"
    assert _date("20240320") == "20240320"


def test_str_helper_handles_nan():
    from finance_data.provider.akshare.lhb.history import _str
    assert _str(float("nan")) == ""
    assert _str(None) == ""
    assert _str("平安银行") == "平安银行"
