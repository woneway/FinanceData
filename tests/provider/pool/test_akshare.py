"""股票池 akshare provider 测试"""
from unittest.mock import patch
import pandas as pd
import pytest

from finance_data.provider.pool.akshare import (
    get_zt_pool,
    get_strong_stocks,
    get_previous_zt,
    get_zbgc_pool,
)
from finance_data.provider.types import DataResult, DataFetchError


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def zt_pool_df():
    return pd.DataFrame([{
        "序号": 1, "代码": "000001", "名称": "平安银行",
        "涨跌幅": 10.02, "最新价": 12.34,
        "成交额": 5e8, "流通市值": 2e11, "总市值": 3e11,
        "换手率": 8.5, "封板资金": 1e8,
        "首次封板时间": "093012", "最后封板时间": "150000",
        "炸板次数": 0, "连板数": 1, "所属行业": "银行",
        "涨停统计": "1/10",
    }])


@pytest.fixture
def strong_stocks_df():
    return pd.DataFrame([{
        "序号": 1, "代码": "600519", "名称": "贵州茅台",
        "涨跌幅": 5.5, "最新价": 1800.0, "涨停价": 1890.0,
        "成交额": 3e9, "流通市值": 2e12, "总市值": 2.5e12,
        "换手率": 0.5, "量比": 2.3,
        "是否新高": "是", "入选理由": "60日新高", "所属行业": "食品饮料",
    }])


@pytest.fixture
def previous_zt_df():
    return pd.DataFrame([{
        "序号": 1, "代码": "002230", "名称": "科大讯飞",
        "涨跌幅": -2.0, "最新价": 45.0, "涨停价": 49.0,
        "成交额": 8e8, "流通市值": 5e10, "总市值": 6e10,
        "换手率": 3.2,
        "昨日封板时间": "143512", "昨日连板数": 2, "所属行业": "计算机",
    }])


@pytest.fixture
def zbgc_pool_df():
    return pd.DataFrame([{
        "序号": 1, "代码": "300750", "名称": "宁德时代",
        "涨跌幅": 6.0, "最新价": 220.0, "涨停价": 231.0,
        "成交额": 4e9, "流通市值": 1e12, "总市值": 1.5e12,
        "换手率": 1.8, "首次封板时间": "100530",
        "炸板次数": 2, "振幅": 11.5, "所属行业": "电气设备",
    }])


# ── get_zt_pool ────────────────────────────────────────────────────────────────

def test_get_zt_pool_returns_data_result(zt_pool_df):
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_em",
               return_value=zt_pool_df):
        result = get_zt_pool("20260320")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["name"] == "平安银行"
    assert row["price"] == pytest.approx(12.34)
    assert row["amount"] == pytest.approx(5e8)
    assert row["continuous_days"] == 1
    assert row["open_times"] == 0
    assert row["first_seal_time"] == "093012"
    assert row["industry"] == "银行"


def test_get_zt_pool_empty_returns_empty_list():
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_em",
               return_value=pd.DataFrame()):
        result = get_zt_pool("20260101")
    assert result.data == []
    assert result.meta["rows"] == 0


def test_get_zt_pool_continuous_days_ge_1(zt_pool_df):
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_em",
               return_value=zt_pool_df):
        result = get_zt_pool("20260320")
    for row in result.data:
        assert row["continuous_days"] >= 1


def test_get_zt_pool_no_empty_symbol_or_zero_price(zt_pool_df):
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_em",
               return_value=zt_pool_df):
        result = get_zt_pool("20260320")
    for row in result.data:
        assert row["symbol"] != ""
        assert row["price"] > 0


def test_get_zt_pool_network_error():
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_zt_pool("20260320")
    assert exc.value.kind == "network"


def test_get_zt_pool_data_error():
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_em",
               side_effect=ValueError("bad data")):
        with pytest.raises(DataFetchError) as exc:
            get_zt_pool("20260320")
    assert exc.value.kind == "data"


# ── get_strong_stocks ─────────────────────────────────────────────────────────

def test_get_strong_stocks_returns_data_result(strong_stocks_df):
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_strong_em",
               return_value=strong_stocks_df):
        result = get_strong_stocks("20260320")
    assert isinstance(result, DataResult)
    assert len(result.data) == 1
    row = result.data[0]
    assert row["symbol"] == "600519"
    assert row["is_new_high"] is True
    assert row["reason"] == "60日新高"
    assert row["volume_ratio"] == pytest.approx(2.3)


def test_get_strong_stocks_is_new_high_false():
    df = pd.DataFrame([{
        "代码": "000002", "名称": "万科A",
        "涨跌幅": 3.0, "最新价": 10.0, "涨停价": 11.0,
        "成交额": 1e8, "流通市值": 1e11, "总市值": 1.2e11,
        "换手率": 2.0, "量比": 1.5,
        "是否新高": "否", "入选理由": "量比放大", "所属行业": "房地产",
    }])
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_strong_em",
               return_value=df):
        result = get_strong_stocks("20260320")
    assert result.data[0]["is_new_high"] is False


def test_get_strong_stocks_empty_returns_empty_list():
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_strong_em",
               return_value=pd.DataFrame()):
        result = get_strong_stocks("20260101")
    assert result.data == []


def test_get_strong_stocks_no_empty_symbol_or_zero_price(strong_stocks_df):
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_strong_em",
               return_value=strong_stocks_df):
        result = get_strong_stocks("20260320")
    for row in result.data:
        assert row["symbol"] != ""
        assert row["price"] > 0


def test_get_strong_stocks_network_error():
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_strong_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_strong_stocks("20260320")
    assert exc.value.kind == "network"


# ── get_previous_zt ───────────────────────────────────────────────────────────

def test_get_previous_zt_returns_data_result(previous_zt_df):
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_previous_em",
               return_value=previous_zt_df):
        result = get_previous_zt("20260321")
    assert isinstance(result, DataResult)
    assert len(result.data) == 1
    row = result.data[0]
    assert row["symbol"] == "002230"
    assert row["pct_change"] == pytest.approx(-2.0)
    assert row["prev_seal_time"] == "143512"
    assert row["prev_continuous_days"] == 2


def test_get_previous_zt_empty_returns_empty_list():
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_previous_em",
               return_value=pd.DataFrame()):
        result = get_previous_zt("20260101")
    assert result.data == []


def test_get_previous_zt_no_empty_symbol_or_zero_price(previous_zt_df):
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_previous_em",
               return_value=previous_zt_df):
        result = get_previous_zt("20260321")
    for row in result.data:
        assert row["symbol"] != ""
        assert row["price"] > 0


def test_get_previous_zt_network_error():
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_previous_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_previous_zt("20260321")
    assert exc.value.kind == "network"


# ── get_zbgc_pool ─────────────────────────────────────────────────────────────

def test_get_zbgc_pool_returns_data_result(zbgc_pool_df):
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_zbgc_em",
               return_value=zbgc_pool_df):
        result = get_zbgc_pool("20260320")
    assert isinstance(result, DataResult)
    assert len(result.data) == 1
    row = result.data[0]
    assert row["symbol"] == "300750"
    assert row["open_times"] == 2
    assert row["amplitude"] == pytest.approx(11.5)
    assert row["first_seal_time"] == "100530"


def test_get_zbgc_pool_empty_returns_empty_list():
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_zbgc_em",
               return_value=pd.DataFrame()):
        result = get_zbgc_pool("20260101")
    assert result.data == []


def test_get_zbgc_pool_no_empty_symbol_or_zero_price(zbgc_pool_df):
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_zbgc_em",
               return_value=zbgc_pool_df):
        result = get_zbgc_pool("20260320")
    for row in result.data:
        assert row["symbol"] != ""
        assert row["price"] > 0


def test_get_zbgc_pool_network_error():
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_zbgc_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_zbgc_pool("20260320")
    assert exc.value.kind == "network"


# ── helper edge cases ──────────────────────────────────────────────────────────

def test_bool_from_str_handles_various_values():
    from finance_data.provider.pool.akshare import _bool_from_str
    assert _bool_from_str("是") is True
    assert _bool_from_str("否") is False
    assert _bool_from_str("True") is True
    assert _bool_from_str("false") is False
    assert _bool_from_str(True) is True
    assert _bool_from_str(float("nan")) is False
    assert _bool_from_str(None) is False


def test_zt_pool_handles_nan_fields():
    """NaN 字段应安全转换为默认值而不是崩溃。"""
    df = pd.DataFrame([{
        "代码": "000001", "名称": "平安银行",
        "涨跌幅": float("nan"), "最新价": 12.0,
        "成交额": 5e8, "流通市值": 2e11, "总市值": 3e11,
        "换手率": float("nan"), "封板资金": float("nan"),
        "首次封板时间": float("nan"), "最后封板时间": float("nan"),
        "炸板次数": float("nan"), "连板数": 1, "所属行业": "银行",
    }])
    with patch("finance_data.provider.pool.akshare.ak.stock_zt_pool_em",
               return_value=df):
        result = get_zt_pool("20260320")
    row = result.data[0]
    assert row["pct_change"] == 0.0
    assert row["first_seal_time"] == ""
    assert row["open_times"] == 0
