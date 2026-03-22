from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from finance_data.provider.index.tushare import get_index_quote, get_index_history
from finance_data.provider.types import DataResult, DataFetchError


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


def test_get_index_quote_returns_data_result(mock_pro, mock_daily_df):
    mock_pro.index_daily.return_value = mock_daily_df
    with patch("finance_data.provider.index.tushare._get_pro", return_value=mock_pro):
        result = get_index_quote("000001.SH")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert result.data[0]["price"] == 3100.0


def test_get_index_history_returns_data_result(mock_pro, mock_daily_df):
    mock_pro.index_daily.return_value = mock_daily_df
    with patch("finance_data.provider.index.tushare._get_pro", return_value=mock_pro):
        result = get_index_history("000001.SH", start="20240101", end="20240102")
    assert isinstance(result, DataResult)
    assert result.data[0]["close"] == 3100.0


def test_get_index_quote_empty_raises(mock_pro):
    mock_pro.index_daily.return_value = pd.DataFrame()
    with patch("finance_data.provider.index.tushare._get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            get_index_quote("INVALID.SH")
    assert exc.value.kind == "data"
