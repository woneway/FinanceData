"""验证所有 realtime provider 的 timestamp 含时区信息"""
from unittest.mock import patch, MagicMock
import pandas as pd


def test_tushare_realtime_timestamp_has_timezone():
    from finance_data.provider.tushare.realtime.realtime import TushareRealtimeQuote

    mock_df = pd.DataFrame([{
        "close": 15.5, "pct_chg": 1.2, "vol": 500.0, "amount": 775.0,
    }])

    with patch("finance_data.provider.tushare.realtime.realtime.get_pro") as mock_pro:
        pro = MagicMock()
        pro.daily.return_value = mock_df
        mock_pro.return_value = pro
        result = TushareRealtimeQuote().get_realtime_quote("000001")

    ts = result.data[0]["timestamp"]
    assert "+08:00" in ts, f"timestamp 应含时区 +08:00，got: {ts}"


def test_tushare_index_timestamp_has_timezone():
    from finance_data.provider.tushare.index.realtime import TushareIndexQuote

    mock_df = pd.DataFrame([{
        "close": 3200.0, "pct_chg": 0.5, "vol": 3e8, "amount": 4e6,
    }])

    with patch("finance_data.provider.tushare.index.realtime.get_pro") as mock_pro:
        pro = MagicMock()
        pro.index_daily.return_value = mock_df
        mock_pro.return_value = pro
        result = TushareIndexQuote().get_index_quote_realtime("000001.SH")

    ts = result.data[0]["timestamp"]
    assert "+08:00" in ts, f"timestamp 应含时区 +08:00，got: {ts}"
