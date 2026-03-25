"""验证 tushare realtime volume 单位转换 + meta 标注"""
from unittest.mock import patch, MagicMock
import pandas as pd
from finance_data.provider.tushare.realtime.realtime import TushareRealtimeQuote


def test_tushare_realtime_volume_converts_hand_to_shares():
    """tushare vol=500（手）应转换为 volume=50000（股）"""
    mock_df = pd.DataFrame([{
        "close": 15.5,
        "pct_chg": 1.2,
        "vol": 500.0,  # 500 手
        "amount": 775.0,  # 千元
    }])

    with patch("finance_data.provider.tushare.realtime.realtime.get_pro") as mock_pro:
        pro = MagicMock()
        pro.daily.return_value = mock_df
        mock_pro.return_value = pro

        provider = TushareRealtimeQuote()
        result = provider.get_realtime_quote("000001")

    quote = result.data[0]
    assert quote["volume"] == 50000.0, f"Expected 50000 (股), got {quote['volume']}"
    assert quote["amount"] == 775000.0
    # meta 应标注 price 为 EOD close
    assert result.meta.get("price_type") == "eod_close"
