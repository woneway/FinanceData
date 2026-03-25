"""验证 tushare kline/index 返回数据为升序（oldest first）"""
from unittest.mock import patch, MagicMock
import pandas as pd
from finance_data.provider.tushare.kline.history import TushareKlineHistory
from finance_data.provider.tushare.index.history import TushareIndexHistory


def test_tushare_kline_sorted_ascending():
    """tushare kline 返回数据应按日期升序"""
    # 模拟 tushare 默认降序返回
    mock_df = pd.DataFrame([
        {"trade_date": "20240103", "open": 11, "high": 12, "low": 10, "close": 11.5, "vol": 100, "amount": 1000, "pct_chg": 1.0},
        {"trade_date": "20240102", "open": 10, "high": 11, "low": 9.5, "close": 10.5, "vol": 80, "amount": 800, "pct_chg": 0.5},
        {"trade_date": "20240101", "open": 10, "high": 10.5, "low": 9.8, "close": 10.0, "vol": 60, "amount": 600, "pct_chg": -0.2},
    ])

    with patch("finance_data.provider.tushare.kline.history.get_pro") as mock_pro:
        pro = MagicMock()
        pro.daily.return_value = mock_df
        mock_pro.return_value = pro

        result = TushareKlineHistory().get_kline_history("000001", "daily", "20240101", "20240103")

    dates = [bar["date"] for bar in result.data]
    assert dates == ["20240101", "20240102", "20240103"], f"Expected ascending, got {dates}"


def test_tushare_index_sorted_ascending():
    """tushare index 返回数据应按日期升序"""
    mock_df = pd.DataFrame([
        {"trade_date": "20240103", "open": 3100, "high": 3150, "low": 3080, "close": 3120, "vol": 3e8, "amount": 4e6, "pct_chg": 0.3},
        {"trade_date": "20240102", "open": 3050, "high": 3100, "low": 3020, "close": 3080, "vol": 2.5e8, "amount": 3.5e6, "pct_chg": 0.5},
        {"trade_date": "20240101", "open": 3000, "high": 3060, "low": 2990, "close": 3050, "vol": 2e8, "amount": 3e6, "pct_chg": -0.1},
    ])

    with patch("finance_data.provider.tushare.index.history.get_pro") as mock_pro:
        pro = MagicMock()
        pro.index_daily.return_value = mock_df
        mock_pro.return_value = pro

        result = TushareIndexHistory().get_index_history("000001.SH", "20240101", "20240103")

    dates = [bar["date"] for bar in result.data]
    assert dates == ["20240101", "20240102", "20240103"], f"Expected ascending, got {dates}"
