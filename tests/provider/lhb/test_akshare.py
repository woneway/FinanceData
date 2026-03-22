"""龙虎榜 akshare provider 测试"""
import math
from unittest.mock import patch
import pandas as pd
import pytest

from finance_data.provider.lhb.akshare import (
    get_lhb_detail,
    get_lhb_stock_stat,
    get_lhb_active_traders,
    get_lhb_trader_stat,
    get_lhb_stock_detail,
)
from finance_data.provider.types import DataResult, DataFetchError


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
def lhb_stock_stat_df():
    return pd.DataFrame([{
        "序号": 1, "代码": "000001", "名称": "平安银行",
        "最近上榜日": "2024-03-20", "收盘价": 10.5, "涨跌幅": 5.2,
        "上榜次数": 3,
        "龙虎榜净买额": 2e6, "龙虎榜买入额": 8e6,
        "龙虎榜卖出额": 6e6, "龙虎榜总成交额": 1.4e7,
        "买方机构次数": 2, "卖方机构次数": 1, "机构买入净额": 1e6,
        "机构买入总额": 3e6, "机构卖出总额": 2e6,
        "近1个月涨跌幅": 5.0, "近3个月涨跌幅": 10.0,
        "近6个月涨跌幅": 15.0, "近1年涨跌幅": 20.0,
    }])


@pytest.fixture
def lhb_active_trader_df():
    return pd.DataFrame([{
        "序号": 1, "营业部名称": "华宝证券上海东大名路营业部",
        "上榜日": "2024-03-20",
        "买入个股数": 5.0, "卖出个股数": 3.0,
        "买入总金额": 1e7, "卖出总金额": 6e6, "总买卖净额": 4e6,
        "买入股票": "平安银行 招商银行 贵州茅台",
    }])


@pytest.fixture
def lhb_active_trader_nan_stocks_df():
    """买入股票字段为 NaN（纯卖出方营业部）"""
    return pd.DataFrame([{
        "序号": 1, "营业部名称": "某卖出营业部",
        "上榜日": "2024-03-20",
        "买入个股数": 0.0, "卖出个股数": 2.0,
        "买入总金额": 0.0, "卖出总金额": 3e6, "总买卖净额": -3e6,
        "买入股票": float("nan"),
    }])


@pytest.fixture
def lhb_trader_stat_df():
    return pd.DataFrame([{
        "序号": 1, "营业部名称": "华宝证券上海东大名路营业部",
        "龙虎榜成交金额": 2e8, "上榜次数": 46,
        "买入额": 1.2e8, "买入次数": 46,
        "卖出额": 8e7, "卖出次数": 42,
    }])


@pytest.fixture
def lhb_stock_detail_buy_df():
    return pd.DataFrame([{
        "序号": 1, "交易营业部名称": "华宝证券上海东大名路营业部",
        "买入金额": 5e6, "买入金额-占总成交比例": 5.0,
        "卖出金额-占总成交比例": 0.0, "净额": 5e6,
        "类型": "日涨幅偏离值达到7%的前5只证券",
    }])


@pytest.fixture
def lhb_stock_detail_sell_df():
    return pd.DataFrame([{
        "序号": 1, "交易营业部名称": "华宝证券上海东大名路营业部",
        "卖出金额": 3e6, "买入金额-占总成交比例": 0.0,
        "卖出金额-占总成交比例": 3.0, "净额": -3e6,
        "类型": "日跌幅偏离值达到7%的前5只证券",
    }])


# ── get_lhb_detail ────────────────────────────────────────────────────────────

def test_get_lhb_detail_returns_data_result(lhb_detail_df):
    with patch("finance_data.provider.lhb.akshare.ak.stock_lhb_detail_em",
               return_value=lhb_detail_df):
        result = get_lhb_detail("20240320", "20240320")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["date"] == "20240320"
    assert row["lhb_net_buy"] == 1_000_000


def test_get_lhb_detail_empty_raises():
    with patch("finance_data.provider.lhb.akshare.ak.stock_lhb_detail_em",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            get_lhb_detail("20240101", "20240101")
    assert exc.value.kind == "data"


def test_get_lhb_detail_network_error():
    with patch("finance_data.provider.lhb.akshare.ak.stock_lhb_detail_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_lhb_detail("20240320", "20240320")
    assert exc.value.kind == "network"


# ── get_lhb_stock_stat ────────────────────────────────────────────────────────

def test_get_lhb_stock_stat_returns_data_result(lhb_stock_stat_df):
    with patch("finance_data.provider.lhb.akshare.ak.stock_lhb_stock_statistic_em",
               return_value=lhb_stock_stat_df):
        result = get_lhb_stock_stat("近一月")
    assert isinstance(result, DataResult)
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["times"] == 3
    assert row["inst_buy_times"] == 2


def test_get_lhb_stock_stat_empty_raises():
    with patch("finance_data.provider.lhb.akshare.ak.stock_lhb_stock_statistic_em",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError):
            get_lhb_stock_stat()


def test_get_lhb_stock_stat_invalid_period():
    with pytest.raises(DataFetchError) as exc:
        get_lhb_stock_stat("近两月")
    assert exc.value.kind == "data"
    assert "period" in exc.value.reason


# ── get_lhb_active_traders ────────────────────────────────────────────────────

def test_get_lhb_active_traders_returns_data_result(lhb_active_trader_df):
    with patch("finance_data.provider.lhb.akshare.ak.stock_lhb_hyyyb_em",
               return_value=lhb_active_trader_df):
        result = get_lhb_active_traders("20240320", "20240320")
    assert isinstance(result, DataResult)
    row = result.data[0]
    assert row["branch_name"] == "华宝证券上海东大名路营业部"
    assert row["buy_count"] == 5
    assert row["net_amount"] == 4e6
    assert row["stocks"] == "平安银行 招商银行 贵州茅台"


def test_get_lhb_active_traders_nan_stocks(lhb_active_trader_nan_stocks_df):
    """NaN 买入股票字段应返回空字符串，而不是 'nan'。"""
    with patch("finance_data.provider.lhb.akshare.ak.stock_lhb_hyyyb_em",
               return_value=lhb_active_trader_nan_stocks_df):
        result = get_lhb_active_traders("20240320", "20240320")
    assert result.data[0]["stocks"] == ""


def test_get_lhb_active_traders_empty_raises():
    with patch("finance_data.provider.lhb.akshare.ak.stock_lhb_hyyyb_em",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError):
            get_lhb_active_traders("20240320", "20240320")


# ── get_lhb_trader_stat ───────────────────────────────────────────────────────

def test_get_lhb_trader_stat_returns_data_result(lhb_trader_stat_df):
    with patch("finance_data.provider.lhb.akshare.ak.stock_lhb_traderstatistic_em",
               return_value=lhb_trader_stat_df):
        result = get_lhb_trader_stat("近一月")
    assert isinstance(result, DataResult)
    row = result.data[0]
    assert row["branch_name"] == "华宝证券上海东大名路营业部"
    assert row["times"] == 46
    assert row["buy_times"] == 46


def test_get_lhb_trader_stat_empty_raises():
    with patch("finance_data.provider.lhb.akshare.ak.stock_lhb_traderstatistic_em",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError):
            get_lhb_trader_stat()


def test_get_lhb_trader_stat_invalid_period():
    with pytest.raises(DataFetchError) as exc:
        get_lhb_trader_stat("近两年")
    assert exc.value.kind == "data"


# ── get_lhb_stock_detail ──────────────────────────────────────────────────────

def test_get_lhb_stock_detail_buy_flag(lhb_stock_detail_buy_df):
    with patch("finance_data.provider.lhb.akshare.ak.stock_lhb_stock_detail_em",
               return_value=lhb_stock_detail_buy_df):
        result = get_lhb_stock_detail("000001", "20240320", "买入")
    assert isinstance(result, DataResult)
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["flag"] == "买入"
    assert row["branch_name"] == "华宝证券上海东大名路营业部"
    assert row["trade_amount"] == 5e6   # 买入方向读"买入金额"列
    assert row["buy_rate"] == 5.0
    assert row["sell_rate"] == 0.0


def test_get_lhb_stock_detail_sell_flag(lhb_stock_detail_sell_df):
    """flag='卖出' 时，trade_amount 应读取'卖出金额'列而非'买入金额'列。"""
    with patch("finance_data.provider.lhb.akshare.ak.stock_lhb_stock_detail_em",
               return_value=lhb_stock_detail_sell_df):
        result = get_lhb_stock_detail("000001", "20240320", "卖出")
    row = result.data[0]
    assert row["flag"] == "卖出"
    assert row["trade_amount"] == 3e6   # 卖出方向读"卖出金额"列
    assert row["net_amount"] == pytest.approx(-3e6)


def test_get_lhb_stock_detail_empty_raises():
    with patch("finance_data.provider.lhb.akshare.ak.stock_lhb_stock_detail_em",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError):
            get_lhb_stock_detail("000001", "20240320", "买入")


# ── helper edge cases ──────────────────────────────────────────────────────────

def test_int_helper_handles_inf():
    """_int 对 inf 应返回默认值而不是抛出 OverflowError。"""
    from finance_data.provider.lhb.akshare import _int
    assert _int(float("inf")) == 0
    assert _int(float("-inf")) == 0
    assert _int(float("nan")) == 0


def test_date_helper_handles_none():
    from finance_data.provider.lhb.akshare import _date
    assert _date(None) == ""
    assert _date("2024-03-20") == "20240320"
    assert _date("20240320") == "20240320"


def test_str_helper_handles_nan():
    from finance_data.provider.lhb.akshare import _str
    assert _str(float("nan")) == ""
    assert _str(None) == ""
    assert _str("平安银行") == "平安银行"
