"""雪球 K 线历史测试"""
from unittest.mock import MagicMock, patch

import pytest
import requests

from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.xueqiu.kline.history import XueqiuKlineHistory


@pytest.fixture
def provider():
    return XueqiuKlineHistory()


@pytest.fixture
def mock_kline_response():
    """模拟 kline.json 正常响应"""
    return {
        "data": {
            "symbol": "SZ000001",
            "column": [
                "timestamp", "volume", "open", "high", "low", "close",
                "chg", "percent", "turnoverrate", "amount",
            ],
            "item": [
                [1700000000000, 1000000, 12.0, 12.8, 11.9, 12.5, 0.3, 2.46, 0.52, 12500000],
                [1700086400000, 800000, 12.5, 13.0, 12.3, 12.8, 0.3, 2.40, 0.41, 10240000],
            ],
        },
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


class TestXueqiuKlineHistory:
    @patch.dict("os.environ", {"XUEQIU_COOKIE": "xq_a_token=test"}, clear=False)
    def test_returns_data_result(self, provider, mock_kline_response):
        session = _mock_session(mock_kline_response)
        with patch("finance_data.provider.xueqiu.kline.history.get_session",
                    return_value=session):
            result = provider.get_kline_history(
                "000001", "daily", "20231101", "20231130"
            )
        assert isinstance(result, DataResult)
        assert result.source == "xueqiu"
        assert len(result.data) == 2

    @patch.dict("os.environ", {"XUEQIU_COOKIE": "xq_a_token=test"}, clear=False)
    def test_bars_sorted_by_date(self, provider, mock_kline_response):
        session = _mock_session(mock_kline_response)
        with patch("finance_data.provider.xueqiu.kline.history.get_session",
                    return_value=session):
            result = provider.get_kline_history(
                "000001", "daily", "20231101", "20231130"
            )
        dates = [bar["date"] for bar in result.data]
        assert dates == sorted(dates)

    @patch.dict("os.environ", {"XUEQIU_COOKIE": "xq_a_token=test"}, clear=False)
    def test_fields_mapped_correctly(self, provider, mock_kline_response):
        session = _mock_session(mock_kline_response)
        with patch("finance_data.provider.xueqiu.kline.history.get_session",
                    return_value=session):
            result = provider.get_kline_history(
                "000001", "daily", "20231101", "20231130"
            )
        bar = result.data[0]
        assert bar["symbol"] == "000001"
        assert bar["open"] == 12.0
        assert bar["high"] == 12.8
        assert bar["low"] == 11.9
        assert bar["close"] == 12.5
        assert bar["volume"] == 1000000
        assert bar["amount"] == 12500000
        assert bar["pct_chg"] == 2.46
        assert bar["adj"] == "qfq"

    def test_no_cookie_raises_auth_error(self, provider):
        with patch.dict("os.environ", {}, clear=False), \
             patch("finance_data.provider.xueqiu.kline.history.has_login_cookie",
                   return_value=False):
            with pytest.raises(DataFetchError) as exc:
                provider.get_kline_history(
                    "000001", "daily", "20231101", "20231130"
                )
        assert exc.value.kind == "auth"
        assert exc.value.source == "xueqiu"

    @patch.dict("os.environ", {"XUEQIU_COOKIE": "xq_a_token=test"}, clear=False)
    def test_unsupported_period_raises(self, provider):
        with pytest.raises(DataFetchError) as exc:
            provider.get_kline_history("000001", "1min", "20231101", "20231130")
        assert exc.value.kind == "data"

    @patch.dict("os.environ", {"XUEQIU_COOKIE": "xq_a_token=test"}, clear=False)
    def test_network_error_raises(self, provider):
        session = MagicMock(spec=requests.Session)
        session.get.side_effect = ConnectionError("refused")
        with patch("finance_data.provider.xueqiu.kline.history.get_session",
                    return_value=session):
            with pytest.raises(DataFetchError) as exc:
                provider.get_kline_history(
                    "000001", "daily", "20231101", "20231130"
                )
        assert exc.value.kind == "network"

    @patch.dict("os.environ", {"XUEQIU_COOKIE": "xq_a_token=test"}, clear=False)
    def test_empty_response_retries_then_fails(self, provider):
        empty_resp = {"data": {"column": [], "item": []}, "error_code": 0}
        session = _mock_session(empty_resp)
        with patch("finance_data.provider.xueqiu.kline.history.get_session",
                    return_value=session), \
             patch("finance_data.provider.xueqiu.kline.history.refresh_session",
                   return_value=session):
            with pytest.raises(DataFetchError) as exc:
                provider.get_kline_history(
                    "000001", "daily", "20231101", "20231130"
                )
        assert exc.value.kind == "data"

    @patch.dict("os.environ", {"XUEQIU_COOKIE": "xq_a_token=test"}, clear=False)
    def test_weekly_period_mapped(self, provider, mock_kline_response):
        session = _mock_session(mock_kline_response)
        with patch("finance_data.provider.xueqiu.kline.history.get_session",
                    return_value=session):
            provider.get_kline_history(
                "000001", "weekly", "20231101", "20231130"
            )
        call_args = session.get.call_args
        assert call_args[1]["params"]["period"] == "week"

    @patch.dict("os.environ", {"XUEQIU_COOKIE": "xq_a_token=test"}, clear=False)
    def test_http_400_raises_auth_error(self, provider):
        session = MagicMock(spec=requests.Session)
        resp = MagicMock()
        resp.status_code = 400
        http_err = requests.HTTPError(response=resp)
        resp.raise_for_status.side_effect = http_err
        session.get.return_value = resp
        with patch("finance_data.provider.xueqiu.kline.history.get_session",
                    return_value=session), \
             patch("finance_data.provider.xueqiu.kline.history.refresh_session",
                   return_value=session):
            with pytest.raises(DataFetchError) as exc:
                provider.get_kline_history(
                    "000001", "daily", "20231101", "20231130"
                )
        assert exc.value.kind == "auth"
