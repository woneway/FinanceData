"""龙虎榜 tushare provider 测试"""
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from finance_data.provider.lhb.tushare import (
    get_lhb_detail,
    get_lhb_stock_stat,
    get_lhb_active_traders,
    get_lhb_trader_stat,
    get_lhb_stock_detail,
)
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_pro():
    return MagicMock()


@pytest.fixture
def top_list_df():
    return pd.DataFrame([{
        "ts_code": "000001.SZ", "trade_date": "20240320", "name": "平安银行",
        "close": 10.5, "pct_chg": 5.2,
        "turnover_rate": 2.5, "amount": 10000.0,  # 万元
        "l_sell": 400.0, "l_buy": 500.0, "l_amount": 900.0,
        "net_amount": 100.0, "net_rate": 1.0, "amount_rate": 9.0,
        "float_values": 500.0,  # 亿元
        "reason": "日涨幅偏离值达到7%的前5只证券",
    }])


def test_get_lhb_detail_returns_data_result(mock_pro, top_list_df):
    mock_pro.top_list.return_value = top_list_df
    with patch("finance_data.provider.lhb.tushare._get_pro", return_value=mock_pro):
        result = get_lhb_detail("20240320", "20240320")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["date"] == "20240320"
    assert row["pct_change"] == pytest.approx(5.2)   # 验证 pct_chg 字段映射
    # 万元 → 元
    assert row["lhb_net_buy"] == pytest.approx(100.0 * 10_000)
    assert row["market_amount"] == pytest.approx(10000.0 * 10_000)
    # 亿元 → 元
    assert row["float_value"] == pytest.approx(500.0 * 1e8)


def test_get_lhb_detail_empty_raises(mock_pro):
    mock_pro.top_list.return_value = pd.DataFrame()
    with patch("finance_data.provider.lhb.tushare._get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            get_lhb_detail("20240320", "20240320")
    assert exc.value.kind == "data"


def test_get_lhb_detail_no_token():
    with patch.dict("os.environ", {"TUSHARE_TOKEN": ""}):
        with pytest.raises(DataFetchError) as exc:
            get_lhb_detail("20240320", "20240320")
    assert exc.value.kind == "auth"


def test_get_lhb_stock_stat_raises_not_supported():
    with pytest.raises(DataFetchError) as exc:
        get_lhb_stock_stat()
    assert exc.value.kind == "data"


def test_get_lhb_active_traders_raises_not_supported():
    with pytest.raises(DataFetchError) as exc:
        get_lhb_active_traders("20240320", "20240320")
    assert exc.value.kind == "data"


def test_get_lhb_trader_stat_raises_not_supported():
    with pytest.raises(DataFetchError) as exc:
        get_lhb_trader_stat()
    assert exc.value.kind == "data"


def test_get_lhb_stock_detail_raises_not_supported():
    with pytest.raises(DataFetchError) as exc:
        get_lhb_stock_detail("000001", "20240320", "买入")
    assert exc.value.kind == "data"
