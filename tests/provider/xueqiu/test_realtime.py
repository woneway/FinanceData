"""雪球实时行情测试"""
from unittest.mock import MagicMock, patch

import pytest
import requests

from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.xueqiu.realtime.realtime import XueqiuRealtimeQuote


@pytest.fixture
def provider():
    return XueqiuRealtimeQuote()


@pytest.fixture
def mock_quotec_response():
    """模拟 quotec.json 正常响应"""
    return {
        "data": [
            {
                "symbol": "SZ000001",
                "current": 12.5,
                "percent": 1.2,
                "volume": 1000000,
                "amount": 12500000.0,
                "market_capital": 2420000000000.0,
                "pe_ttm": 6.5,
                "pb": 0.8,
                "turnover_rate": 0.52,
                "timestamp": 1700000000000,
            }
        ],
        "error_code": 0,
    }


def _mock_session(json_data, status_code=200):
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    session.get.return_value = resp
    return session


class TestXueqiuRealtimeQuote:
    def test_returns_data_result(self, provider, mock_quotec_response):
        session = _mock_session(mock_quotec_response)
        with patch("finance_data.provider.xueqiu.realtime.realtime.get_session",
                    return_value=session):
            result = provider.get_realtime_quote("000001")
        assert isinstance(result, DataResult)
        assert result.source == "xueqiu"
        assert len(result.data) == 1

    def test_fields_mapped_correctly(self, provider, mock_quotec_response):
        session = _mock_session(mock_quotec_response)
        with patch("finance_data.provider.xueqiu.realtime.realtime.get_session",
                    return_value=session):
            result = provider.get_realtime_quote("000001")
        row = result.data[0]
        assert row["symbol"] == "000001"
        assert row["price"] == 12.5
        assert row["pct_chg"] == 1.2
        assert row["volume"] == 1000000
        assert row["amount"] == 12500000.0
        assert row["market_cap"] == 2420000000000.0
        assert row["pe"] == 6.5
        assert row["pb"] == 0.8
        assert row["turnover_rate"] == 0.52

    def test_sh_symbol_conversion(self, provider, mock_quotec_response):
        mock_quotec_response["data"][0]["symbol"] = "SH600519"
        session = _mock_session(mock_quotec_response)
        with patch("finance_data.provider.xueqiu.realtime.realtime.get_session",
                    return_value=session):
            provider.get_realtime_quote("600519")
        call_args = session.get.call_args
        assert call_args[1]["params"]["symbol"] == "SH600519"

    def test_network_error_raises(self, provider):
        session = MagicMock(spec=requests.Session)
        session.get.side_effect = ConnectionError("timeout")
        with patch("finance_data.provider.xueqiu.realtime.realtime.get_session",
                    return_value=session):
            with pytest.raises(DataFetchError) as exc:
                provider.get_realtime_quote("000001")
        assert exc.value.kind == "network"
        assert exc.value.source == "xueqiu"

    def test_empty_data_retries_then_fails(self, provider):
        empty_resp = {"data": [], "error_code": 0}
        session = _mock_session(empty_resp)
        with patch("finance_data.provider.xueqiu.realtime.realtime.get_session",
                    return_value=session), \
             patch("finance_data.provider.xueqiu.realtime.realtime.refresh_session",
                   return_value=session):
            with pytest.raises(DataFetchError) as exc:
                provider.get_realtime_quote("000001")
        assert exc.value.kind == "data"

    def test_none_values_handled(self, provider):
        """部分字段为 None 时不报错"""
        data = {
            "data": [
                {
                    "symbol": "SZ000001",
                    "current": 12.5,
                    "percent": 1.0,
                    "volume": 100,
                    "amount": 1250.0,
                    "market_capital": None,
                    "pe_ttm": None,
                    "pb": None,
                    "turnover_rate": None,
                    "timestamp": 1700000000000,
                }
            ],
        }
        session = _mock_session(data)
        with patch("finance_data.provider.xueqiu.realtime.realtime.get_session",
                    return_value=session):
            result = provider.get_realtime_quote("000001")
        row = result.data[0]
        assert row["market_cap"] is None
        assert row["pe"] is None
