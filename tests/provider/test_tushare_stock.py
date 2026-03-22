from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from finance_data.provider.tushare.stock import get_stock_info
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_tushare_stock_basic():
    """mock tushare 返回的 DataFrame"""
    return pd.DataFrame([{
        "ts_code": "000001.SZ",
        "name": "平安银行",
        "industry": "银行",
        "list_date": "19910403",
        "area": "深圳",
        "market": "主板",
    }])


def test_get_stock_info_returns_data_result(mock_tushare_stock_basic):
    mock_pro = MagicMock()
    mock_pro.stock_basic.return_value = mock_tushare_stock_basic

    with patch("finance_data.provider.tushare.stock._get_pro", return_value=mock_pro):
        result = get_stock_info("000001")

    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert len(result.data) == 1
    assert result.data[0]["name"] == "平安银行"


def test_get_stock_info_meta_contains_rows(mock_tushare_stock_basic):
    mock_pro = MagicMock()
    mock_pro.stock_basic.return_value = mock_tushare_stock_basic

    with patch("finance_data.provider.tushare.stock._get_pro", return_value=mock_pro):
        result = get_stock_info("000001")

    assert result.meta["rows"] == 1
    assert result.meta["symbol"] == "000001"


def test_get_stock_info_empty_result_raises_data_fetch_error():
    mock_pro = MagicMock()
    mock_pro.stock_basic.return_value = pd.DataFrame()

    with patch("finance_data.provider.tushare.stock._get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc_info:
            get_stock_info("INVALID")

    assert exc_info.value.kind == "data"
    assert exc_info.value.source == "tushare"


def test_get_stock_info_auth_error_raises_data_fetch_error():
    mock_pro = MagicMock()
    mock_pro.stock_basic.side_effect = Exception("无权限访问该接口")

    with patch("finance_data.provider.tushare.stock._get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc_info:
            get_stock_info("000001")

    assert exc_info.value.kind == "auth"


def test_get_stock_info_network_error_raises_data_fetch_error():
    mock_pro = MagicMock()
    mock_pro.stock_basic.side_effect = ConnectionError("timeout")

    with patch("finance_data.provider.tushare.stock._get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc_info:
            get_stock_info("000001")

    assert exc_info.value.kind == "network"


def test_get_stock_info_missing_token_raises_data_fetch_error():
    with patch("finance_data.provider.tushare.stock._get_pro",
               side_effect=DataFetchError("tushare", "init", "TUSHARE_TOKEN 未设置", "auth")):
        with pytest.raises(DataFetchError) as exc_info:
            get_stock_info("000001")

    assert exc_info.value.kind == "auth"
