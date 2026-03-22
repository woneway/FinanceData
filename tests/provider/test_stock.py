from unittest.mock import patch
import pandas as pd
import pytest

from finance_data.provider.akshare.stock import get_stock_info
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_akshare_stock_info():
    """mock akshare 返回的 DataFrame"""
    return pd.DataFrame([
        {"item": "股票代码", "value": "000001"},
        {"item": "股票简称", "value": "平安银行"},
        {"item": "行业", "value": "银行"},
        {"item": "上市时间", "value": "19910403"},
    ])


def test_get_stock_info_returns_data_result(mock_akshare_stock_info):
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_info_em",
               return_value=mock_akshare_stock_info):
        result = get_stock_info("000001")

    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 4
    assert result.data[0]["item"] == "股票代码"


def test_get_stock_info_meta_contains_rows(mock_akshare_stock_info):
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_info_em",
               return_value=mock_akshare_stock_info):
        result = get_stock_info("000001")

    assert result.meta["rows"] == 4
    assert result.meta["symbol"] == "000001"


def test_get_stock_info_network_error_raises_data_fetch_error():
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_info_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc_info:
            get_stock_info("000001")

    assert exc_info.value.kind == "network"
    assert exc_info.value.source == "akshare"


def test_get_stock_info_data_error_raises_data_fetch_error():
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_info_em",
               side_effect=Exception("股票代码不存在")):
        with pytest.raises(DataFetchError) as exc_info:
            get_stock_info("INVALID")

    assert exc_info.value.kind == "data"
