"""验证 tushare index history volume 从手转换为股"""
from unittest.mock import patch, MagicMock
import pandas as pd


def test_tushare_index_history_volume_in_shares():
    """tushare index_daily vol 为手，IndexBar.volume 应为股 (×100)"""
    from finance_data.provider.tushare.index.history import TushareIndexHistory

    mock_df = pd.DataFrame([{
        "trade_date": "20260324",
        "open": 3200.0, "high": 3250.0, "low": 3180.0, "close": 3230.0,
        "vol": 500.0,  # 手
        "amount": 4000.0,  # 千元
        "pct_chg": 0.5,
    }])

    with patch("finance_data.provider.tushare.index.history.get_pro") as mock_pro:
        pro = MagicMock()
        pro.index_daily.return_value = mock_df
        mock_pro.return_value = pro
        result = TushareIndexHistory().get_index_history(
            symbol="000001.SH", start="20260324", end="20260324",
        )

    bar = result.data[0]
    # vol=500 手 × 100 = 50000 股
    assert bar["volume"] == 50000, f"volume 应为 50000 股，got: {bar['volume']}"
    # amount=4000 千元 × 1000 = 4000000 元
    assert bar["amount"] == 4_000_000, f"amount 应为 4000000 元，got: {bar['amount']}"
