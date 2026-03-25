"""验证 tushare lhb detail 支持日期范围查询"""
from unittest.mock import patch, MagicMock, call
import pandas as pd


def test_tushare_lhb_date_range_queries_multiple_days():
    """start_date != end_date 时应逐日查询并合并"""
    from finance_data.provider.tushare.lhb.history import TushareLhbDetail

    df1 = pd.DataFrame([{
        "ts_code": "000001.SZ", "name": "平安银行", "trade_date": "20260323",
        "close": 10.0, "pct_chg": 1.0, "net_amount": 1.0, "l_buy": 2.0,
        "l_sell": 1.0, "l_amount": 3.0, "amount": 100.0,
        "net_rate": 0.5, "amount_rate": 0.3, "turnover_rate": 5.0,
        "float_values": 10.0, "reason": "涨幅偏离",
    }])
    df2 = pd.DataFrame([{
        "ts_code": "600519.SH", "name": "贵州茅台", "trade_date": "20260324",
        "close": 1800.0, "pct_chg": 2.0, "net_amount": 5.0, "l_buy": 8.0,
        "l_sell": 3.0, "l_amount": 11.0, "amount": 500.0,
        "net_rate": 1.0, "amount_rate": 0.8, "turnover_rate": 3.0,
        "float_values": 200.0, "reason": "涨幅偏离",
    }])
    empty_df = pd.DataFrame()

    with patch("finance_data.provider.tushare.lhb.history.get_pro") as mock_pro:
        pro = MagicMock()
        # 20260323(Mon) -> data, 20260324(Tue) -> data, 20260325(Wed) in range but we only query 23-24
        pro.top_list.side_effect = [df1, df2]
        mock_pro.return_value = pro
        result = TushareLhbDetail().get_lhb_detail_history("20260323", "20260324")

    # 应合并两天的结果
    assert len(result.data) == 2, f"应有2条记录，got: {len(result.data)}"
    symbols = {r["symbol"] for r in result.data}
    assert symbols == {"000001", "600519"}, f"got symbols: {symbols}"
    # 应调用两次 top_list
    assert pro.top_list.call_count == 2


def test_tushare_lhb_single_date_works():
    """start_date == end_date 时仍正常工作"""
    from finance_data.provider.tushare.lhb.history import TushareLhbDetail

    df1 = pd.DataFrame([{
        "ts_code": "000001.SZ", "name": "平安银行", "trade_date": "20260323",
        "close": 10.0, "pct_chg": 1.0, "net_amount": 1.0, "l_buy": 2.0,
        "l_sell": 1.0, "l_amount": 3.0, "amount": 100.0,
        "net_rate": 0.5, "amount_rate": 0.3, "turnover_rate": 5.0,
        "float_values": 10.0, "reason": "涨幅偏离",
    }])

    with patch("finance_data.provider.tushare.lhb.history.get_pro") as mock_pro:
        pro = MagicMock()
        pro.top_list.return_value = df1
        mock_pro.return_value = pro
        result = TushareLhbDetail().get_lhb_detail_history("20260323", "20260323")

    assert len(result.data) == 1
    assert pro.top_list.call_count == 1
