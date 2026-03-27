"""跨 provider 单位一致性验证

对同一接口的不同 provider，注入各自上游格式的 mock 数据，
验证转换后的 volume/amount 单位一致（股/元）。

各上游原始单位:
- tushare: vol=手(×100→股), amount=千元(×1000→元)
- akshare 腾讯: amount=千元(×1000→元), volume=估算
- xueqiu: volume=股, amount=元 (直出)
"""
from unittest.mock import patch, MagicMock
import pandas as pd


# ========== Kline ==========

def test_kline_tushare_vs_xueqiu_units():
    """tushare 和 xueqiu kline 输出单位一致: volume=股, amount=元"""
    from finance_data.provider.tushare.kline.history import TushareKlineHistory
    from finance_data.provider.xueqiu.kline.history import XueqiuKlineHistory

    # 相同的「真实」数据: 10000 股, 100000 元
    expected_volume = 10000.0
    expected_amount = 100000.0

    # tushare: vol=100 手, amount=100 千元
    ts_df = pd.DataFrame([{
        "trade_date": "20260324",
        "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2,
        "vol": 100.0, "amount": 100.0, "pct_chg": 0.5,
    }])

    with patch("finance_data.provider.tushare.kline.history.get_pro") as mp:
        pro = MagicMock()
        pro.daily.return_value = ts_df
        mp.return_value = pro
        ts_result = TushareKlineHistory().get_kline_history(
            "000001", "daily", "20260324", "20260324")

    ts_bar = ts_result.data[0]
    assert ts_bar["volume"] == expected_volume, f"tushare volume: {ts_bar['volume']}"
    assert ts_bar["amount"] == expected_amount, f"tushare amount: {ts_bar['amount']}"

    # xueqiu: volume=10000 股, amount=100000 元 (直出)
    xq_resp = {
        "data": {
            "column": ["timestamp", "volume", "open", "high", "low", "close", "chg", "percent", "turnoverrate", "amount"],
            "item": [[1774335600000, 10000, 10.0, 10.5, 9.8, 10.2, 0.05, 0.5, 1.0, 100000.0]],
        }
    }

    with patch("finance_data.provider.xueqiu.kline.history.get_session") as ms, \
         patch("finance_data.provider.xueqiu.kline.history.has_login_cookie", return_value=True):
        session = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = xq_resp
        session.get.return_value = resp
        ms.return_value = session
        xq_result = XueqiuKlineHistory().get_kline_history(
            "000001", "daily", "20260324", "20260324")

    xq_bar = xq_result.data[0]
    assert xq_bar["volume"] == expected_volume, f"xueqiu volume: {xq_bar['volume']}"
    assert xq_bar["amount"] == expected_amount, f"xueqiu amount: {xq_bar['amount']}"


# ========== Realtime ==========

def test_realtime_tushare_vs_xueqiu_units():
    """tushare 和 xueqiu realtime 输出单位一致: volume=股, amount=元"""
    from finance_data.provider.tushare.realtime.realtime import TushareRealtimeQuote
    from finance_data.provider.xueqiu.realtime.realtime import XueqiuRealtimeQuote

    expected_volume = 50000.0
    expected_amount = 525000.0

    # tushare: vol=500 手, amount=525 千元
    ts_df = pd.DataFrame([{
        "close": 10.5, "pct_chg": 1.0, "vol": 500.0, "amount": 525.0,
    }])

    with patch("finance_data.provider.tushare.realtime.realtime.get_pro") as mp:
        pro = MagicMock()
        pro.daily.return_value = ts_df
        mp.return_value = pro
        ts_result = TushareRealtimeQuote().get_realtime_quote("000001")

    ts_q = ts_result.data[0]
    assert ts_q["volume"] == expected_volume, f"tushare volume: {ts_q['volume']}"
    assert ts_q["amount"] == expected_amount, f"tushare amount: {ts_q['amount']}"

    # xueqiu: volume=50000 股, amount=525000 元
    xq_data = {
        "data": [{
            "symbol": "SZ000001", "name": "平安银行",
            "current": 10.5, "percent": 1.0,
            "volume": 50000, "amount": 525000.0,
            "market_capital": None, "pe_ttm": None, "pb": None,
            "turnover_rate": None, "timestamp": 1711267200000,
        }]
    }

    with patch("finance_data.provider.xueqiu.realtime.realtime.get_session") as ms:
        session = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = xq_data
        resp.raise_for_status = MagicMock()
        session.get.return_value = resp
        ms.return_value = session
        xq_result = XueqiuRealtimeQuote().get_realtime_quote("000001")

    xq_q = xq_result.data[0]
    assert xq_q["volume"] == expected_volume, f"xueqiu volume: {xq_q['volume']}"
    assert xq_q["amount"] == expected_amount, f"xueqiu amount: {xq_q['amount']}"


# ========== Index Realtime ==========

def test_index_realtime_tushare_vs_xueqiu_units():
    """tushare 和 xueqiu index realtime volume/amount 一致"""
    from finance_data.provider.tushare.index.realtime import TushareIndexQuote
    from finance_data.provider.xueqiu.index.realtime import XueqiuIndexQuote

    expected_volume = 80000.0
    expected_amount = 256000000.0

    # tushare: vol=800 手, amount=256000 千元
    ts_df = pd.DataFrame([{
        "close": 3200.0, "pct_chg": 0.5,
        "vol": 800.0, "amount": 256000.0,
    }])

    with patch("finance_data.provider.tushare.index.realtime.get_pro") as mp:
        pro = MagicMock()
        pro.index_daily.return_value = ts_df
        mp.return_value = pro
        ts_result = TushareIndexQuote().get_index_quote_realtime("000001.SH")

    ts_q = ts_result.data[0]
    assert ts_q["volume"] == expected_volume, f"tushare volume: {ts_q['volume']}"
    assert ts_q["amount"] == expected_amount, f"tushare amount: {ts_q['amount']}"

    # xueqiu: volume=80000 股, amount=256000000 元
    xq_data = {
        "data": [{
            "symbol": "SH000001", "name": "上证指数",
            "current": 3200.0, "percent": 0.5,
            "volume": 80000, "amount": 256000000.0,
            "timestamp": 1711267200000,
        }]
    }

    with patch("finance_data.provider.xueqiu.index.realtime.get_session") as ms:
        session = MagicMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = xq_data
        resp.raise_for_status = MagicMock()
        session.get.return_value = resp
        ms.return_value = session
        xq_result = XueqiuIndexQuote().get_index_quote_realtime("000001.SH")

    xq_q = xq_result.data[0]
    assert xq_q["volume"] == expected_volume, f"xueqiu volume: {xq_q['volume']}"
    assert xq_q["amount"] == expected_amount, f"xueqiu amount: {xq_q['amount']}"


# ========== Index History ==========

def test_index_history_tushare_units():
    """tushare index history: volume=股 (手×100), amount=元 (千元×1000)"""
    from finance_data.provider.tushare.index.history import TushareIndexHistory

    ts_df = pd.DataFrame([{
        "trade_date": "20260324",
        "open": 3200.0, "high": 3250.0, "low": 3180.0, "close": 3230.0,
        "vol": 500.0, "amount": 4000.0, "pct_chg": 0.5,
    }])

    with patch("finance_data.provider.tushare.index.history.get_pro") as mp:
        pro = MagicMock()
        pro.index_daily.return_value = ts_df
        mp.return_value = pro
        result = TushareIndexHistory().get_index_history("000001.SH", "20260324", "20260324")

    bar = result.data[0]
    assert bar["volume"] == 50000.0, f"tushare index volume should be 50000 股, got: {bar['volume']}"
    assert bar["amount"] == 4000000.0, f"tushare index amount should be 4000000 元, got: {bar['amount']}"


def test_kline_akshare_volume_and_amount_unit():
    """akshare kline 腾讯源: 'amount'列实为成交量(手)，volume=手*100，amount=估算"""
    from finance_data.provider.akshare.kline.history import AkshareKlineHistory

    mock_df = pd.DataFrame([{
        "date": "2026-03-24",
        "open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5,
        "amount": 50.0,  # 实为 50 手
    }])

    with patch("finance_data.provider.akshare.kline.history.ak") as mock_ak:
        mock_ak.stock_zh_a_hist_tx.return_value = mock_df
        result = AkshareKlineHistory().get_kline_history(
            "000001", "daily", "20260324", "20260324")

    bar = result.data[0]
    # volume = 50 手 * 100 = 5000 股
    assert bar["volume"] == 5000, f"volume should be 5000 股, got: {bar['volume']}"
    # amount = 5000 * (10+11+9.5+10.5)/4 = 5000 * 10.25 = 51250
    assert bar["amount"] == 51250.0, f"amount should be 51250 元, got: {bar['amount']}"
