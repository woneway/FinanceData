"""验证 akshare index history volume/amount 转换

腾讯源 "amount" 列实际为成交量（手），非成交额（千元）。
volume = raw * 100（手→股），指数成交额无法从腾讯源获取，设为 0。
"""
from unittest.mock import patch
import pandas as pd
from finance_data.provider.akshare.index.history import AkshareIndexHistory


def test_akshare_index_volume_from_tencent():
    """腾讯源 amount 实为成交量(手)，volume=raw*100(股)，amount=0"""
    mock_df = pd.DataFrame([
        {"date": "2024-01-02", "open": 3000.0, "close": 3010.0,
         "high": 3020.0, "low": 2990.0, "amount": 100.0},  # 100 手
        {"date": "2024-01-03", "open": 3010.0, "close": 3050.0,
         "high": 3060.0, "low": 3000.0, "amount": 200.0},  # 200 手
    ])

    with patch("finance_data.provider.akshare.index.history.ak") as mock_ak:
        mock_ak.stock_zh_index_daily_tx.return_value = mock_df

        provider = AkshareIndexHistory()
        result = provider.get_index_history("000001.SH", "20240103", "20240103")

    bar = result.data[0]
    # volume = 200 手 * 100 = 20000 股
    assert bar["volume"] == 20000, f"Expected 20000 (股), got {bar['volume']}"
    # 指数成交额无法从腾讯源获取
    assert bar["amount"] == 0.0, f"Expected 0.0, got {bar['amount']}"
