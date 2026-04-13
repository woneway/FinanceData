from unittest.mock import patch

import pandas as pd
import pytest

from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.pool.limit_list import TushareLimitList


@pytest.fixture
def mock_df():
    return pd.DataFrame([{
        "trade_date": "20260410",
        "ts_code": "600105.SH",
        "name": "永鼎股份",
        "price": 38.1,
        "pct_chg": 9.99,
        "limit_type": "涨停池",
        "open_num": 0,
        "lu_desc": "共封装光学",
        "tag": "首板",
        "status": "一字板",
        "limit_order": 100000.0,
        "limit_amount": 50000.0,
        "turnover_rate": 5.0,
        "limit_up_suc_rate": 80.0,
    }])


def test_returns_data_result(mock_df):
    provider = TushareLimitList()
    mock_pro = type("MockPro", (), {"limit_list_ths": lambda self, **kw: mock_df})()
    with patch("finance_data.provider.tushare.pool.limit_list.get_pro", return_value=mock_pro):
        result = provider.get_limit_list("20260410", "涨停池")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert len(result.data) == 1
    assert result.data[0]["symbol"] == "600105.SH"
    assert result.data[0]["lu_desc"] == "共封装光学"


def test_empty_raises():
    provider = TushareLimitList()
    mock_pro = type("MockPro", (), {"limit_list_ths": lambda self, **kw: pd.DataFrame()})()
    with patch("finance_data.provider.tushare.pool.limit_list.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            provider.get_limit_list("20260410")
    assert exc.value.kind == "data"
