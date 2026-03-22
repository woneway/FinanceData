from unittest.mock import patch
import pandas as pd
import pytest

from finance_data.provider.akshare.stock import get_stock_info
from finance_data.provider.models import StockInfo
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_xueqiu_df():
    """mock 雪球接口返回的 DataFrame"""
    return pd.DataFrame([
        {"item": "org_short_name_cn", "value": "平安银行"},
        {"item": "affiliate_industry", "value": {"ind_code": "BK0055", "ind_name": "银行"}},
        {"item": "listed_date", "value": 670608000000},
        {"item": "provincial_name", "value": "广东省"},
    ])


def test_get_stock_info_returns_data_result(mock_xueqiu_df):
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_basic_info_xq",
               return_value=mock_xueqiu_df):
        result = get_stock_info("000001")

    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1


def test_get_stock_info_data_matches_stock_info_schema(mock_xueqiu_df):
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_basic_info_xq",
               return_value=mock_xueqiu_df):
        result = get_stock_info("000001")

    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["name"] == "平安银行"
    assert row["industry"] == "银行"
    assert row["list_date"] == "19910403"
    assert row["area"] == "广东省"
    assert "market" in row


def test_get_stock_info_meta(mock_xueqiu_df):
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_basic_info_xq",
               return_value=mock_xueqiu_df):
        result = get_stock_info("000001")

    assert result.meta["symbol"] == "000001"
    assert result.meta["rows"] == 1


def test_get_stock_info_network_error():
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_basic_info_xq",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_stock_info("000001")

    assert exc.value.kind == "network"
    assert exc.value.source == "akshare"


def test_get_stock_info_data_error():
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_basic_info_xq",
               side_effect=Exception("股票代码不存在")):
        with pytest.raises(DataFetchError) as exc:
            get_stock_info("INVALID")

    assert exc.value.kind == "data"
