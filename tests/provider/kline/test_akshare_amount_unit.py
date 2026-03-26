"""验证 akshare kline (腾讯源) volume/amount 转换

腾讯源 "amount" 列实际为成交量（手），非成交额（千元）。
volume = raw * 100（手→股），amount 由 volume * 均价估算。
"""
from unittest.mock import patch
import pandas as pd


def test_akshare_kline_tencent_volume_and_amount():
    """腾讯源 amount 实为成交量(手)，volume=raw*100(股)，amount=volume*avg(估算)"""
    from finance_data.provider.akshare.kline.history import AkshareKlineHistory

    mock_df = pd.DataFrame([{
        "date": "2026-03-24",
        "open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5,
        "amount": 100.0,  # 实为 100 手
    }])

    with patch("finance_data.provider.akshare.kline.history.ak") as mock_ak:
        mock_ak.stock_zh_a_hist_tx.return_value = mock_df
        result = AkshareKlineHistory().get_kline_history(
            symbol="000001", period="daily",
            start="20260324", end="20260324", adj="qfq",
        )

    bar = result.data[0]
    # volume = 100 手 * 100 = 10000 股
    assert bar["volume"] == 10000, f"volume 应为 10000 股，got: {bar['volume']}"
    # amount = 10000 * (10+11+9.5+10.5)/4 = 10000 * 10.25 = 102500
    assert bar["amount"] == 102500.0, f"amount 应为 102500 元，got: {bar['amount']}"
