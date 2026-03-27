"""龙虎榜 akshare 新浪源 - 单元测试"""
from unittest.mock import patch, MagicMock
import pandas as pd


def test_lhb_stock_stat_sina():
    """AkshareLhbStockStat 使用 stock_lhb_ggtj_sina 并正确映射列"""
    from finance_data.provider.akshare.lhb.history import AkshareLhbStockStat

    mock_df = pd.DataFrame([{
        "股票代码": "688498",
        "股票名称": "源杰科技",
        "上榜次数": 3,
        "累积购买额": 720930.10,
        "累积卖出额": 481126.00,
        "净额": 239804.10,
        "买入席位数": 6,
        "卖出席位数": 4,
    }])

    with patch("finance_data.provider.akshare.lhb.history.ak") as mock_ak:
        mock_ak.stock_lhb_ggtj_sina.return_value = mock_df
        result = AkshareLhbStockStat().get_lhb_stock_stat_history("近一月")

    assert result.source == "akshare"
    row = result.data[0]
    assert row["symbol"] == "688498"
    assert row["name"] == "源杰科技"
    assert row["times"] == 3
    assert row["lhb_buy"] == 720930.10
    assert row["lhb_sell"] == 481126.00
    assert row["lhb_net_buy"] == 239804.10
    assert row["inst_buy_times"] == 6
    assert row["inst_sell_times"] == 4


def test_lhb_active_traders_sina():
    """AkshareLhbActiveTraders 使用 stock_lhb_yytj_sina 并正确映射列"""
    from finance_data.provider.akshare.lhb.history import AkshareLhbActiveTraders

    mock_df = pd.DataFrame([{
        "营业部名称": "中国国际金融股份有限公司上海分公司",
        "上榜次数": 37,
        "累积购买额": 58283.70,
        "买入席位数": 21,
        "累积卖出额": 71878.04,
        "卖出席位数": 16,
        "买入前三股票": "金开新能,国城矿业,顺钠股份,",
    }])

    with patch("finance_data.provider.akshare.lhb.history.ak") as mock_ak:
        mock_ak.stock_lhb_yytj_sina.return_value = mock_df
        result = AkshareLhbActiveTraders().get_lhb_active_traders_history("20260320", "20260327")

    row = result.data[0]
    assert row["branch_name"] == "中国国际金融股份有限公司上海分公司"
    assert row["buy_count"] == 37
    assert row["buy_amount"] == 58283.70
    assert row["sell_amount"] == 71878.04
    assert row["net_amount"] == 58283.70 - 71878.04
    assert "金开新能" in row["stocks"]


def test_lhb_trader_stat_sina():
    """AkshareLhbTraderStat 使用 stock_lhb_yytj_sina 并正确映射列"""
    from finance_data.provider.akshare.lhb.history import AkshareLhbTraderStat

    mock_df = pd.DataFrame([{
        "营业部名称": "华泰证券深圳前海营业部",
        "上榜次数": 27,
        "累积购买额": 75234.31,
        "买入席位数": 13,
        "累积卖出额": 52047.05,
        "卖出席位数": 14,
        "买入前三股票": "立讯精密,金开新能,",
    }])

    with patch("finance_data.provider.akshare.lhb.history.ak") as mock_ak:
        mock_ak.stock_lhb_yytj_sina.return_value = mock_df
        result = AkshareLhbTraderStat().get_lhb_trader_stat_history("近一月")

    row = result.data[0]
    assert row["branch_name"] == "华泰证券深圳前海营业部"
    assert row["times"] == 27
    assert row["buy_amount"] == 75234.31
    assert row["buy_times"] == 13
    assert row["sell_amount"] == 52047.05
    assert row["sell_times"] == 14
    assert row["lhb_amount"] == 75234.31 + 52047.05


def test_lhb_stock_detail_sina():
    """AkshareLhbStockDetail 使用 stock_lhb_detail_daily_sina 并正确映射列"""
    from finance_data.provider.akshare.lhb.history import AkshareLhbStockDetail

    mock_df = pd.DataFrame([{
        "序号": 1,
        "股票代码": "000533",
        "股票名称": "顺钠股份",
        "收盘价": 15.53,
        "对应值": -8.54,
        "成交量": 13890.2625,
        "成交额": 221754.4429,
        "指标": "跌幅偏离值达7%的证券",
    }])

    with patch("finance_data.provider.akshare.lhb.history.ak") as mock_ak:
        mock_ak.stock_lhb_detail_daily_sina.return_value = mock_df
        result = AkshareLhbStockDetail().get_lhb_stock_detail_history("", "20260326", "买入")

    row = result.data[0]
    assert row["symbol"] == "000533"
    assert row["date"] == "20260326"
    assert row["trade_amount"] == 221754.4429
    assert row["seat_type"] == "跌幅偏离值达7%的证券"
    assert row["flag"] == "全部"
