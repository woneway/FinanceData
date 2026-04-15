"""全市场日频基本面 tushare provider 测试"""
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from finance_data.provider.tushare.daily_basic.history import TushareDailyBasicMarket
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def mock_pro():
    return MagicMock()


@pytest.fixture
def basic_df():
    return pd.DataFrame([{
        "ts_code": "000001.SZ", "trade_date": "20260414",
        "close": 11.17, "turnover_rate": 0.85, "turnover_rate_f": 1.02,
        "volume_ratio": 0.93, "pe_ttm": 4.56, "pb": 0.52,
        "total_mv": 218000.0, "circ_mv": 195000.0,
    }])


def test_returns_data_result(mock_pro, basic_df):
    mock_pro.daily_basic.return_value = basic_df
    with patch("finance_data.provider.tushare.daily_basic.history.get_pro", return_value=mock_pro):
        result = TushareDailyBasicMarket().get_daily_basic_market("20260414")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    row = result.data[0]
    assert row["symbol"] == "000001.SZ"
    assert row["turnover_rate"] == pytest.approx(0.85)
    assert row["total_mv"] == pytest.approx(218000.0 * 10000)
    assert row["circ_mv"] == pytest.approx(195000.0 * 10000)


def test_empty_raises(mock_pro):
    mock_pro.daily_basic.return_value = pd.DataFrame()
    with patch("finance_data.provider.tushare.daily_basic.history.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            TushareDailyBasicMarket().get_daily_basic_market("20260414")
    assert exc.value.kind == "data"


def test_network_error_raises(mock_pro):
    mock_pro.daily_basic.side_effect = TimeoutError("read timed out")
    with patch("finance_data.provider.tushare.daily_basic.history.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            TushareDailyBasicMarket().get_daily_basic_market("20260414")
    assert exc.value.kind == "network"
