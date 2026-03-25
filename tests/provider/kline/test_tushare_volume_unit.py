"""验证 tushare kline volume 单位转换（手→股）"""
from unittest.mock import patch, MagicMock
import pandas as pd
from finance_data.provider.tushare.kline.history import TushareKlineHistory


def test_tushare_kline_volume_converts_hand_to_shares():
    """tushare vol=100（手）应转换为 volume=10000（股）"""
    mock_df = pd.DataFrame([{
        "trade_date": "20240101",
        "open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5,
        "vol": 100.0,  # 100 手
        "amount": 1050.0,  # 千元
        "pct_chg": 2.5,
    }])

    with patch("finance_data.provider.tushare.kline.history.get_pro") as mock_pro:
        pro = MagicMock()
        pro.daily.return_value = mock_df
        mock_pro.return_value = pro

        provider = TushareKlineHistory()
        result = provider.get_kline_history("000001", "daily", "20240101", "20240101")

    bar = result.data[0]
    assert bar["volume"] == 10000.0, f"Expected 10000 (股), got {bar['volume']}"
    assert bar["amount"] == 1050000.0, "amount should be converted: 千元 * 1000 = 元"
