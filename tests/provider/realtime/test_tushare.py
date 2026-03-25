from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from finance_data.provider.tushare.realtime.realtime import TushareRealtimeQuote
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return TushareRealtimeQuote()


@pytest.fixture
def mock_pro():
    return MagicMock()


@pytest.fixture
def mock_daily_df():
    return pd.DataFrame([{
        "trade_date": "20240102", "close": 12.5, "pct_chg": 1.2,
        "vol": 1000000.0, "amount": 12500000.0,
    }])


def test_get_realtime_quote_returns_data_result(provider, mock_pro, mock_daily_df):
    mock_pro.daily.return_value = mock_daily_df
    with patch("finance_data.provider.tushare.realtime.realtime.get_pro", return_value=mock_pro):
        result = provider.get_realtime_quote("000001")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"


def test_get_realtime_quote_fields(provider, mock_pro, mock_daily_df):
    mock_pro.daily.return_value = mock_daily_df
    with patch("finance_data.provider.tushare.realtime.realtime.get_pro", return_value=mock_pro):
        result = provider.get_realtime_quote("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["price"] == 12.5
    assert row["pct_chg"] == 1.2


def test_get_realtime_quote_empty_raises(provider, mock_pro):
    mock_pro.daily.return_value = pd.DataFrame()
    with patch("finance_data.provider.tushare.realtime.realtime.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            provider.get_realtime_quote("INVALID")
    assert exc.value.kind == "data"


def test_get_realtime_quote_network_error(provider, mock_pro):
    mock_pro.daily.side_effect = ConnectionError("timeout")
    with patch("finance_data.provider.tushare.realtime.realtime.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            provider.get_realtime_quote("000001")
    assert exc.value.kind == "network"
