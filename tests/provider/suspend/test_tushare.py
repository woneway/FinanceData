"""停牌信息 tushare provider 测试"""
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from finance_data.provider.tushare.suspend.history import TushareSuspend
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def mock_pro():
    return MagicMock()


@pytest.fixture
def suspend_df():
    return pd.DataFrame([{
        "ts_code": "688531.SH", "trade_date": "20260414",
        "suspend_type": "S",
    }])


def test_returns_data_result(mock_pro, suspend_df):
    mock_pro.suspend_d.return_value = suspend_df
    with patch("finance_data.provider.tushare.suspend.history.get_pro", return_value=mock_pro):
        result = TushareSuspend().get_suspend_history("20260414")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    row = result.data[0]
    assert row["symbol"] == "688531.SH"
    assert row["suspend_date"] == "20260414"
    assert row["suspend_reason"] == "S"


def test_empty_raises(mock_pro):
    mock_pro.suspend_d.return_value = pd.DataFrame()
    with patch("finance_data.provider.tushare.suspend.history.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            TushareSuspend().get_suspend_history("20260414")
    assert exc.value.kind == "data"


def test_network_error_raises(mock_pro):
    mock_pro.suspend_d.side_effect = TimeoutError("connection timed out")
    with patch("finance_data.provider.tushare.suspend.history.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            TushareSuspend().get_suspend_history("20260414")
    assert exc.value.kind == "network"
