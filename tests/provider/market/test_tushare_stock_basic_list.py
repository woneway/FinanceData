"""全市场股票列表 tushare provider 测试"""
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from finance_data.provider.tushare.stock.basic_list import TushareStockBasicList
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def mock_pro():
    return MagicMock()


@pytest.fixture
def basic_list_df():
    return pd.DataFrame([
        {"ts_code": "000001.SZ", "name": "平安银行", "industry": "银行", "market": "主板", "list_date": "19910403"},
        {"ts_code": "000005.SZ", "name": "*ST星源", "industry": "环境保护", "market": "主板", "list_date": "19901210"},
    ])


def test_returns_data_result(mock_pro, basic_list_df):
    mock_pro.stock_basic.return_value = basic_list_df
    with patch("finance_data.provider.tushare.stock.basic_list.get_pro", return_value=mock_pro):
        result = TushareStockBasicList().get_stock_basic_list("L")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert len(result.data) == 2
    assert result.data[0]["is_st"] is False
    assert result.data[1]["is_st"] is True
    assert result.data[1]["name"] == "*ST星源"


def test_empty_raises(mock_pro):
    mock_pro.stock_basic.return_value = pd.DataFrame()
    with patch("finance_data.provider.tushare.stock.basic_list.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            TushareStockBasicList().get_stock_basic_list("L")
    assert exc.value.kind == "data"


def test_network_error_raises(mock_pro):
    mock_pro.stock_basic.side_effect = ConnectionError("refused")
    with patch("finance_data.provider.tushare.stock.basic_list.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            TushareStockBasicList().get_stock_basic_list("L")
    assert exc.value.kind == "network"
