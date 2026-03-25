from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from finance_data.provider.tushare.index.realtime import TushareIndexQuote
from finance_data.provider.tushare.index.history import TushareIndexHistory
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def quote_provider():
    return TushareIndexQuote()


@pytest.fixture
def history_provider():
    return TushareIndexHistory()


@pytest.fixture
def mock_pro():
    return MagicMock()


@pytest.fixture
def mock_daily_df():
    return pd.DataFrame([{
        "trade_date": "20240102", "open": 3090.0, "high": 3110.0,
        "low": 3085.0, "close": 3100.0, "vol": 1e10,
        "amount": 1e12, "pct_chg": 0.5,
    }])


def test_get_index_quote_returns_data_result(quote_provider, mock_pro, mock_daily_df):
    mock_pro.index_daily.return_value = mock_daily_df
    with patch("finance_data.provider.tushare.index.realtime.get_pro", return_value=mock_pro):
        result = quote_provider.get_index_quote_realtime("000001.SH")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert result.data[0]["price"] == 3100.0


def test_get_index_history_returns_data_result(history_provider, mock_pro, mock_daily_df):
    mock_pro.index_daily.return_value = mock_daily_df
    with patch("finance_data.provider.tushare.index.history.get_pro", return_value=mock_pro):
        result = history_provider.get_index_history("000001.SH", start="20240101", end="20240102")
    assert isinstance(result, DataResult)
    assert result.data[0]["close"] == 3100.0


def test_get_index_quote_empty_raises(quote_provider, mock_pro):
    mock_pro.index_daily.return_value = pd.DataFrame()
    with patch("finance_data.provider.tushare.index.realtime.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            quote_provider.get_index_quote_realtime("INVALID.SH")
    assert exc.value.kind == "data"
