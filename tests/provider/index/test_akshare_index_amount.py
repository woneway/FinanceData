"""验证 akshare index history amount 单位转换（千元→元）"""
from unittest.mock import patch
import pandas as pd
from finance_data.provider.akshare.index.history import AkshareIndexHistory


def test_akshare_index_amount_converts_qian_to_yuan():
    """akshare amount=200（千元）应转换为 200000（元）"""
    mock_df = pd.DataFrame([
        {"date": "2024-01-02", "open": 3000.0, "close": 3010.0,
         "high": 3020.0, "low": 2990.0, "amount": 100.0},  # 100 千元
        {"date": "2024-01-03", "open": 3010.0, "close": 3050.0,
         "high": 3060.0, "low": 3000.0, "amount": 200.0},  # 200 千元
    ])

    with patch("finance_data.provider.akshare.index.history.ak") as mock_ak:
        mock_ak.stock_zh_index_daily_tx.return_value = mock_df

        provider = AkshareIndexHistory()
        result = provider.get_index_history("000001.SH", "20240103", "20240103")

    bar = result.data[0]
    assert bar["amount"] == 200000.0, f"Expected 200000 (元), got {bar['amount']}"
