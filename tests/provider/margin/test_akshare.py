from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.margin.akshare import get_margin, get_margin_detail
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_sse_df():
    return pd.DataFrame([{
        "信用交易日期": "20240301",
        "融资余额": 9e11,
        "融资买入额": 5e10,
        "融券余量金额": 1e10,
        "融券卖出量": 1e7,
        "融资融券余额": 1e12,
        "融券余量": 5e8,
    }])


@pytest.fixture
def mock_szse_df():
    return pd.DataFrame([{
        "融资买入额": 321.08,
        "融资余额": 7077.67,
        "融券卖出量": 0.28,
        "融券余量": 24.34,
        "融券余额": 157.3,
        "融资融券余额": 7234.97,
    }])


def test_get_margin_returns_data_result(mock_sse_df, mock_szse_df):
    with patch("finance_data.provider.margin.akshare.ak.stock_margin_sse",
               return_value=mock_sse_df):
        with patch("finance_data.provider.margin.akshare.ak.stock_margin_szse",
                   return_value=mock_szse_df):
            result = get_margin(trade_date="20240301")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 2


def test_get_margin_sse_fields(mock_sse_df, mock_szse_df):
    with patch("finance_data.provider.margin.akshare.ak.stock_margin_sse",
               return_value=mock_sse_df):
        with patch("finance_data.provider.margin.akshare.ak.stock_margin_szse",
                   return_value=mock_szse_df):
            result = get_margin(trade_date="20240301")
    sse = next(r for r in result.data if r["exchange"] == "SSE")
    assert sse["date"] == "20240301"
    assert sse["rzye"] == 9e11
    assert sse["exchange"] == "SSE"


def test_get_margin_szse_converts_yi_to_yuan(mock_sse_df, mock_szse_df):
    with patch("finance_data.provider.margin.akshare.ak.stock_margin_sse",
               return_value=mock_sse_df):
        with patch("finance_data.provider.margin.akshare.ak.stock_margin_szse",
                   return_value=mock_szse_df):
            result = get_margin(trade_date="20240301")
    szse = next(r for r in result.data if r["exchange"] == "SZSE")
    # 7077.67 亿元 -> 707767000000 元
    assert abs(szse["rzye"] - 7077.67 * 1e8) < 1


def test_get_margin_network_error():
    with patch("finance_data.provider.margin.akshare.ak.stock_margin_sse",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_margin(trade_date="20240301")
    assert exc.value.kind == "network"


def test_get_margin_empty_raises():
    with patch("finance_data.provider.margin.akshare.ak.stock_margin_sse",
               return_value=pd.DataFrame()):
        with patch("finance_data.provider.margin.akshare.ak.stock_margin_szse",
                   return_value=pd.DataFrame()):
            with pytest.raises(DataFetchError) as exc:
                get_margin(trade_date="20240301")
    assert exc.value.kind == "data"


# ---- margin_detail tests ----

@pytest.fixture
def mock_margin_detail_df():
    return pd.DataFrame([{
        "标的证券代码": "600000",
        "标的证券简称": "浦发银行",
        "融资余额": 5e8,
        "融资买入额": 1e8,
        "融资偿还额": 5e7,
        "融券卖出量": 1e5,
    }])


def test_get_margin_detail_returns_data(mock_margin_detail_df):
    with patch("finance_data.provider.margin.akshare.ak.stock_margin_detail_sse",
               return_value=mock_margin_detail_df):
        result = get_margin_detail(trade_date="20240301")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1


def test_get_margin_detail_fields(mock_margin_detail_df):
    with patch("finance_data.provider.margin.akshare.ak.stock_margin_detail_sse",
               return_value=mock_margin_detail_df):
        result = get_margin_detail(trade_date="20240301")
    row = result.data[0]
    assert row["date"] == "20240301"
    assert row["symbol"] == "600000"
    assert row["name"] == "浦发银行"
    assert row["rzye"] == 5e8
    assert row["rzmre"] == 1e8
    assert row["rzche"] == 5e7
    assert row["rqmcl"] == 1e5


def test_get_margin_detail_network_error():
    with patch("finance_data.provider.margin.akshare.ak.stock_margin_detail_sse",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_margin_detail(trade_date="20240301")
    assert exc.value.kind == "network"


def test_get_margin_detail_empty_raises():
    with patch("finance_data.provider.margin.akshare.ak.stock_margin_detail_sse",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            get_margin_detail(trade_date="20240301")
    assert exc.value.kind == "data"
