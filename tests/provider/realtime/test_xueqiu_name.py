"""验证 xueqiu realtime/index name 映射正确"""
from finance_data.provider.xueqiu.realtime.realtime import XueqiuRealtimeQuote
from finance_data.provider.xueqiu.index.realtime import XueqiuIndexQuote
from unittest.mock import patch, MagicMock
import requests


def test_xueqiu_realtime_parse_name():
    """name 应为中文名而非 ticker code"""
    provider = XueqiuRealtimeQuote()
    quote = provider._parse("000001", {
        "symbol": "SZ000001",
        "name": "平安银行",
        "current": 15.5,
        "percent": 1.2,
        "volume": 50000,
        "amount": 775000,
        "market_capital": 3e11,
        "pe_ttm": 8.5,
        "pb": 0.9,
        "turnover_rate": 0.5,
        "timestamp": 1700000000000,
    })
    assert quote.name == "平安银行", f"Expected '平安银行', got '{quote.name}'"


def test_xueqiu_index_name():
    """index name 应为中文名而非 ticker code"""
    provider = XueqiuIndexQuote()
    mock_session = MagicMock(spec=requests.Session)
    response = MagicMock()
    response.json.return_value = {
        "data": [{
            "symbol": "SH000001",
            "name": "上证指数",
            "current": 3200.0,
            "percent": 0.5,
            "volume": 300000000,
            "amount": 4500000000,
            "timestamp": 1700000000000,
        }]
    }
    response.raise_for_status = MagicMock()
    mock_session.get.return_value = response

    with patch("finance_data.provider.xueqiu.index.realtime.get_session", return_value=mock_session):
        result = provider.get_index_quote_realtime("000001.SH")

    assert result.data[0]["name"] == "上证指数", \
        f"Expected '上证指数', got '{result.data[0]['name']}'"
