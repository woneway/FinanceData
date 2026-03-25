"""雪球指数（实时 + 历史）测试"""
from unittest.mock import MagicMock, patch

import pytest
import requests

from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.xueqiu.index.realtime import XueqiuIndexQuote
from finance_data.provider.xueqiu.index.history import XueqiuIndexHistory


def _mock_session(json_data, status_code=200):
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    session.get.return_value = resp
    return session


# ---------- 指数实时行情 ----------


@pytest.fixture
def quote_provider():
    return XueqiuIndexQuote()


@pytest.fixture
def mock_index_quotec():
    return {
        "data": [
            {
                "symbol": "SH000001",
                "current": 3100.0,
                "percent": 0.5,
                "volume": 10000000000,
                "amount": 1000000000000.0,
                "timestamp": 1700000000000,
            }
        ],
        "error_code": 0,
    }


class TestXueqiuIndexQuote:
    def test_returns_data_result(self, quote_provider, mock_index_quotec):
        session = _mock_session(mock_index_quotec)
        with patch("finance_data.provider.xueqiu.index.realtime.get_session",
                    return_value=session):
            result = quote_provider.get_index_quote_realtime("000001.SH")
        assert isinstance(result, DataResult)
        assert result.source == "xueqiu"

    def test_fields_mapped(self, quote_provider, mock_index_quotec):
        session = _mock_session(mock_index_quotec)
        with patch("finance_data.provider.xueqiu.index.realtime.get_session",
                    return_value=session):
            result = quote_provider.get_index_quote_realtime("000001.SH")
        row = result.data[0]
        assert row["symbol"] == "000001.SH"
        assert row["price"] == 3100.0
        assert row["pct_chg"] == 0.5

    def test_symbol_conversion(self, quote_provider, mock_index_quotec):
        session = _mock_session(mock_index_quotec)
        with patch("finance_data.provider.xueqiu.index.realtime.get_session",
                    return_value=session):
            quote_provider.get_index_quote_realtime("000001.SH")
        call_args = session.get.call_args
        assert call_args[1]["params"]["symbol"] == "SH000001"

    def test_network_error(self, quote_provider):
        session = MagicMock(spec=requests.Session)
        session.get.side_effect = ConnectionError("timeout")
        with patch("finance_data.provider.xueqiu.index.realtime.get_session",
                    return_value=session):
            with pytest.raises(DataFetchError) as exc:
                quote_provider.get_index_quote_realtime("000001.SH")
        assert exc.value.kind == "network"


# ---------- 指数历史 K 线 ----------


@pytest.fixture
def history_provider():
    return XueqiuIndexHistory()


@pytest.fixture
def mock_index_kline():
    return {
        "data": {
            "symbol": "SH000001",
            "column": ["timestamp", "volume", "open", "high", "low", "close",
                        "chg", "percent", "turnoverrate", "amount"],
            "item": [
                [1700000000000, 1e10, 3090.0, 3110.0, 3085.0, 3100.0, 15, 0.49, 0.0, 1e12],
                [1700086400000, 8e9, 3100.0, 3120.0, 3095.0, 3115.0, 15, 0.48, 0.0, 9e11],
            ],
        },
        "error_code": 0,
    }


class TestXueqiuIndexHistory:
    @patch.dict("os.environ", {"XUEQIU_COOKIE": "xq_a_token=test"}, clear=False)
    def test_returns_data_result(self, history_provider, mock_index_kline):
        session = _mock_session(mock_index_kline)
        with patch("finance_data.provider.xueqiu.index.history.get_session",
                    return_value=session):
            result = history_provider.get_index_history(
                "000001.SH", "20231101", "20231130"
            )
        assert isinstance(result, DataResult)
        assert result.source == "xueqiu"
        assert len(result.data) == 2

    @patch.dict("os.environ", {"XUEQIU_COOKIE": "xq_a_token=test"}, clear=False)
    def test_fields_mapped(self, history_provider, mock_index_kline):
        session = _mock_session(mock_index_kline)
        with patch("finance_data.provider.xueqiu.index.history.get_session",
                    return_value=session):
            result = history_provider.get_index_history(
                "000001.SH", "20231101", "20231130"
            )
        bar = result.data[0]
        assert bar["symbol"] == "000001.SH"
        assert bar["open"] == 3090.0
        assert bar["close"] == 3100.0
        assert bar["pct_chg"] == 0.49

    def test_no_cookie_raises_auth_error(self, history_provider):
        with patch.dict("os.environ", {}, clear=False), \
             patch("finance_data.provider.xueqiu.index.history.has_login_cookie",
                   return_value=False):
            with pytest.raises(DataFetchError) as exc:
                history_provider.get_index_history(
                    "000001.SH", "20231101", "20231130"
                )
        assert exc.value.kind == "auth"

    @patch.dict("os.environ", {"XUEQIU_COOKIE": "xq_a_token=test"}, clear=False)
    def test_network_error(self, history_provider):
        session = MagicMock(spec=requests.Session)
        session.get.side_effect = ConnectionError("refused")
        with patch("finance_data.provider.xueqiu.index.history.get_session",
                    return_value=session):
            with pytest.raises(DataFetchError) as exc:
                history_provider.get_index_history(
                    "000001.SH", "20231101", "20231130"
                )
        assert exc.value.kind == "network"
