"""验证 akshare index history volume/amount 转换

新浪源 stock_zh_index_daily 返回 volume 列（股），amount 不提供（设 0.0）。
"""
from unittest.mock import patch
import pandas as pd
from finance_data.provider.akshare.index.history import AkshareIndexHistory


def test_akshare_index_volume_from_sina():
    """新浪源 volume 直接使用，amount=0.0"""
    mock_df = pd.DataFrame([
        {"date": "2024-01-02", "open": 3000.0, "close": 3010.0,
         "high": 3020.0, "low": 2990.0, "volume": 20000.0},
        {"date": "2024-01-03", "open": 3010.0, "close": 3050.0,
         "high": 3060.0, "low": 3000.0, "volume": 30000.0},
    ])

    with patch("finance_data.provider.akshare.index.history.ak") as mock_ak:
        mock_ak.stock_zh_index_daily.return_value = mock_df

        provider = AkshareIndexHistory()
        result = provider.get_index_history("000001.SH", "20240103", "20240103")

    bar = result.data[0]
    assert bar["volume"] == 30000.0, f"Expected 30000.0, got {bar['volume']}"
    assert bar["amount"] == 0.0, f"Expected 0.0, got {bar['amount']}"
