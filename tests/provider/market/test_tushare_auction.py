from unittest.mock import patch

import pandas as pd
import pytest

from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.market.auction import TushareAuction


def test_returns_data_result():
    df = pd.DataFrame([{
        "ts_code": "000001.SZ", "trade_date": "20260410",
        "vol": 100000, "price": 11.1, "amount": 1110000,
        "pre_close": 11.09, "turnover_rate": 0.5,
        "volume_ratio": 1.2, "float_share": 19400000000,
    }])
    mock_pro = type("MockPro", (), {"stk_auction": lambda self, **kw: df})()
    with patch("finance_data.provider.tushare.market.auction.get_pro", return_value=mock_pro):
        result = TushareAuction().get_auction("20260410")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert result.data[0]["symbol"] == "000001.SZ"
    assert result.data[0]["volume"] == 100000


def test_empty_raises():
    mock_pro = type("MockPro", (), {"stk_auction": lambda self, **kw: pd.DataFrame()})()
    with patch("finance_data.provider.tushare.market.auction.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError):
            TushareAuction().get_auction("20260410")
