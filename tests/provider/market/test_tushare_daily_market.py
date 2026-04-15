"""全市场日线行情 tushare provider 测试"""
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from finance_data.provider.tushare.daily_market.history import TushareDailyMarket
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def mock_pro():
    return MagicMock()


@pytest.fixture
def daily_df():
    return pd.DataFrame([{
        "ts_code": "000001.SZ", "trade_date": "20260414",
        "open": 11.07, "high": 11.17, "low": 11.07, "close": 11.17,
        "pre_close": 11.07, "change": 0.10, "pct_chg": 0.9033,
        "vol": 496151.09, "amount": 551741.633,
    }])


def test_returns_data_result(mock_pro, daily_df):
    mock_pro.daily.return_value = daily_df
    with patch("finance_data.provider.tushare.daily_market.history.get_pro", return_value=mock_pro):
        result = TushareDailyMarket().get_daily_market("20260414")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    row = result.data[0]
    assert row["symbol"] == "000001.SZ"
    assert row["close"] == pytest.approx(11.17)
    assert row["change"] == pytest.approx(0.10)
    assert row["volume"] == pytest.approx(496151.09 * 100)
    assert row["amount"] == pytest.approx(551741.633 * 1000)


def test_empty_raises(mock_pro):
    mock_pro.daily.return_value = pd.DataFrame()
    with patch("finance_data.provider.tushare.daily_market.history.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            TushareDailyMarket().get_daily_market("20260414")
    assert exc.value.kind == "data"


def test_network_error_raises(mock_pro):
    mock_pro.daily.side_effect = ConnectionError("timeout")
    with patch("finance_data.provider.tushare.daily_market.history.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            TushareDailyMarket().get_daily_market("20260414")
    assert exc.value.kind == "network"
