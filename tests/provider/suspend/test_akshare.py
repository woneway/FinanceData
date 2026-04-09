"""停牌信息 akshare provider 测试"""
from unittest.mock import patch
import pandas as pd
import pytest

from finance_data.provider.akshare.suspend.history import AkshareSuspend
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def suspend_df():
    return pd.DataFrame([{
        "序号": 0,
        "代码": "300067",
        "名称": "安诺其",
        "停牌时间": "2026-04-08",
        "停牌截止时间": "2026-04-22",
        "停牌期限": "连续停牌",
        "停牌原因": "拟筹划重大资产重组",
        "所属市场": "深交所创业板",
        "预计复牌时间": "2026-04-22",
    }])


def test_get_suspend_returns_data_result(suspend_df):
    with patch("finance_data.provider.akshare.suspend.history.ak.stock_tfp_em",
               return_value=suspend_df):
        result = AkshareSuspend().get_suspend_history("20260408")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1
    row = result.data[0]
    assert row["symbol"] == "300067"
    assert row["name"] == "安诺其"
    assert row["suspend_date"] == "20260408"
    assert row["resume_date"] == "20260422"
    assert row["suspend_reason"] == "拟筹划重大资产重组"
    assert row["market"] == "深交所创业板"


def test_get_suspend_empty_raises():
    with patch("finance_data.provider.akshare.suspend.history.ak.stock_tfp_em",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            AkshareSuspend().get_suspend_history("20260408")
    assert exc.value.kind == "data"


def test_get_suspend_network_error():
    with patch("finance_data.provider.akshare.suspend.history.ak.stock_tfp_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            AkshareSuspend().get_suspend_history("20260408")
    assert exc.value.kind == "network"
