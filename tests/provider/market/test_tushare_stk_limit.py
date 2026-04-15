"""全市场涨跌停价 tushare provider 测试"""
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from finance_data.provider.tushare.stk_limit.history import TushareStkLimit
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def mock_pro():
    return MagicMock()


@pytest.fixture
def limit_df():
    return pd.DataFrame([{
        "ts_code": "000001.SZ", "trade_date": "20260414",
        "pre_close": 11.07, "up_limit": 12.18, "down_limit": 9.96,
    }])


def test_returns_data_result(mock_pro, limit_df):
    mock_pro.stk_limit.return_value = limit_df
    with patch("finance_data.provider.tushare.stk_limit.history.get_pro", return_value=mock_pro):
        result = TushareStkLimit().get_stk_limit("20260414")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    row = result.data[0]
    assert row["symbol"] == "000001.SZ"
    assert row["up_limit"] == pytest.approx(12.18)
    assert row["down_limit"] == pytest.approx(9.96)


def test_empty_raises(mock_pro):
    mock_pro.stk_limit.return_value = pd.DataFrame()
    with patch("finance_data.provider.tushare.stk_limit.history.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            TushareStkLimit().get_stk_limit("20260414")
    assert exc.value.kind == "data"


def test_network_error_raises(mock_pro):
    mock_pro.stk_limit.side_effect = OSError("network unreachable")
    with patch("finance_data.provider.tushare.stk_limit.history.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            TushareStkLimit().get_stk_limit("20260414")
    assert exc.value.kind == "network"
