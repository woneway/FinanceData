from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.north_flow.tushare import get_north_stock_hold
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_hk_hold_df():
    return pd.DataFrame([{
        "code": "600000",
        "trade_date": "20240301",
        "ts_code": "600000.SH",
        "name": "浦发银行",
        "vol": 1e8,
        "ratio": 2.5,
        "exchange": "SH",
    }])


def test_get_north_stock_hold_returns_data(mock_hk_hold_df):
    with patch("finance_data.provider.north_flow.tushare._get_pro") as mock_pro:
        mock_pro.return_value.hk_hold.return_value = mock_hk_hold_df
        result = get_north_stock_hold(trade_date="20240301")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"


def test_get_north_stock_hold_fields(mock_hk_hold_df):
    with patch("finance_data.provider.north_flow.tushare._get_pro") as mock_pro:
        mock_pro.return_value.hk_hold.return_value = mock_hk_hold_df
        result = get_north_stock_hold(trade_date="20240301")
    row = result.data[0]
    assert row["symbol"] == "600000"
    assert row["name"] == "浦发银行"
    assert row["date"] == "20240301"
    assert row["hold_volume"] == 1e8
    assert row["hold_float_ratio"] == 2.5


def test_get_north_stock_hold_no_token():
    with patch("finance_data.provider.north_flow.tushare.os.environ.get",
               return_value=""):
        with pytest.raises(DataFetchError) as exc:
            get_north_stock_hold(trade_date="20240301")
    assert exc.value.kind == "auth"


def test_get_north_stock_hold_empty_raises(mock_hk_hold_df):
    with patch("finance_data.provider.north_flow.tushare._get_pro") as mock_pro:
        mock_pro.return_value.hk_hold.return_value = pd.DataFrame()
        with pytest.raises(DataFetchError) as exc:
            get_north_stock_hold(trade_date="20240301")
    assert exc.value.kind == "data"
