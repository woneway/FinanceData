from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.tushare.north_flow.history import TushareNorthStockHold
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def mock_hk_hold_df():
    return pd.DataFrame([{
        "code": "600000",
        "trade_date": "20240301",
        "ts_code": "600000.SH",
        "name": "浦发银行",
        "vol": 443245164,
        "ratio": 2.5,
        "exchange": "SH",
    }])


def test_get_north_stock_hold_returns_data(mock_hk_hold_df):
    with patch("finance_data.provider.tushare.north_flow.history.get_pro") as mock_pro:
        mock_pro.return_value.hk_hold.return_value = mock_hk_hold_df
        result = TushareNorthStockHold().get_north_stock_hold_history(
            symbol="", trade_date="20240301"
        )
    assert isinstance(result, DataResult)
    assert result.source == "tushare"


def test_get_north_stock_hold_fields(mock_hk_hold_df):
    with patch("finance_data.provider.tushare.north_flow.history.get_pro") as mock_pro:
        mock_pro.return_value.hk_hold.return_value = mock_hk_hold_df
        result = TushareNorthStockHold().get_north_stock_hold_history(
            symbol="", trade_date="20240301"
        )
    row = result.data[0]
    assert row["symbol"] == "600000"
    assert row["name"] == "浦发银行"
    assert row["date"] == "20240301"
    assert row["hold_volume"] == 443245164
    assert row["hold_ratio"] == 2.5
    assert row["exchange"] == "SH"


def test_get_north_stock_hold_empty_raises():
    with patch("finance_data.provider.tushare.north_flow.history.get_pro") as mock_pro:
        mock_pro.return_value.hk_hold.return_value = pd.DataFrame()
        with pytest.raises(DataFetchError) as exc:
            TushareNorthStockHold().get_north_stock_hold_history(
                symbol="", trade_date="20240301"
            )
    assert exc.value.kind == "data"


def test_exchange_mapping():
    with patch("finance_data.provider.tushare.north_flow.history.get_pro") as mock_pro:
        mock_pro.return_value.hk_hold.return_value = pd.DataFrame([{
            "code": "000001", "trade_date": "20240301", "ts_code": "000001.SZ",
            "name": "平安银行", "vol": 100000000, "ratio": 1.0, "exchange": "SZ",
        }])
        result = TushareNorthStockHold().get_north_stock_hold_history(
            symbol="", trade_date="20240301", exchange="深股通"
        )
    assert result.data[0]["exchange"] == "SZ"
    mock_pro.return_value.hk_hold.assert_called_once_with(
        trade_date="20240301", exchange="SZ"
    )


def test_network_error():
    with patch("finance_data.provider.tushare.north_flow.history.get_pro") as mock_pro:
        mock_pro.return_value.hk_hold.side_effect = ConnectionError("timeout")
        with pytest.raises(DataFetchError) as exc:
            TushareNorthStockHold().get_north_stock_hold_history(
                symbol="", trade_date="20240301"
            )
    assert exc.value.kind == "network"
