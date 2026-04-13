from unittest.mock import patch

import pandas as pd
import pytest

from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.lhb.hm_list import TushareHmList
from finance_data.provider.tushare.lhb.hm_detail import TushareHmDetail


def test_hm_list_returns_data():
    df = pd.DataFrame([{"name": "龙飞虎", "desc": "打板高手", "orgs": '["华泰证券"]'}])
    mock_pro = type("MockPro", (), {"hm_list": lambda self, **kw: df})()
    with patch("finance_data.provider.tushare.lhb.hm_list.get_pro", return_value=mock_pro):
        result = TushareHmList().get_hm_list()
    assert isinstance(result, DataResult)
    assert result.data[0]["name"] == "龙飞虎"


def test_hm_list_empty_raises():
    mock_pro = type("MockPro", (), {"hm_list": lambda self, **kw: pd.DataFrame()})()
    with patch("finance_data.provider.tushare.lhb.hm_list.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError):
            TushareHmList().get_hm_list()


def test_hm_detail_returns_data():
    df = pd.DataFrame([{
        "trade_date": "20260410", "ts_code": "000001.SZ", "ts_name": "平安银行",
        "buy_amount": 1000000, "sell_amount": 500000, "net_amount": 500000,
        "hm_name": "龙飞虎", "hm_orgs": "华泰证券",
    }])
    mock_pro = type("MockPro", (), {"hm_detail": lambda self, **kw: df})()
    with patch("finance_data.provider.tushare.lhb.hm_detail.get_pro", return_value=mock_pro):
        result = TushareHmDetail().get_hm_detail(trade_date="20260410")
    assert isinstance(result, DataResult)
    assert result.data[0]["hm_name"] == "龙飞虎"
    assert result.data[0]["net_amount"] == 500000


def test_hm_detail_empty_raises():
    mock_pro = type("MockPro", (), {"hm_detail": lambda self, **kw: pd.DataFrame()})()
    with patch("finance_data.provider.tushare.lhb.hm_detail.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError):
            TushareHmDetail().get_hm_detail()
