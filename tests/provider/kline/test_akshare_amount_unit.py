"""验证 akshare kline (腾讯源) amount 转换为元"""
from unittest.mock import patch, MagicMock
import pandas as pd


def test_akshare_kline_tencent_amount_in_yuan():
    """腾讯源 amount 原始值为万元，KlineBar.amount 应转换为元"""
    from finance_data.provider.akshare.kline.history import AkshareKlineHistory

    mock_df = pd.DataFrame([{
        "date": "2026-03-24",
        "open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5,
        "amount": 100.0,  # 万元
    }])

    with patch("finance_data.provider.akshare.kline.history.ak") as mock_ak:
        mock_ak.stock_zh_a_hist_tx.return_value = mock_df
        result = AkshareKlineHistory().get_kline_history(
            symbol="000001", period="daily",
            start="20260324", end="20260324", adj="qfq",
        )

    bar = result.data[0]
    # amount 原始 100 万元，应转换为 1,000,000 元
    assert bar["amount"] == 1_000_000, \
        f"amount 应为 1000000 元，got: {bar['amount']}"
