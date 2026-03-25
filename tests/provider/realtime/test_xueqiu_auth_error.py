"""验证 xueqiu HTTP 401/403 归类为 auth 错误"""
import requests
from unittest.mock import MagicMock
from finance_data.interface.types import DataFetchError
from finance_data.provider.xueqiu.realtime.realtime import XueqiuRealtimeQuote
import pytest


def test_xueqiu_401_is_auth_error():
    """HTTP 401 应归类为 auth 错误"""
    mock_session = MagicMock(spec=requests.Session)
    response = MagicMock()
    response.status_code = 401
    response.raise_for_status.side_effect = requests.HTTPError(response=response)
    mock_session.get.return_value = response

    provider = XueqiuRealtimeQuote()
    with pytest.raises(DataFetchError) as exc_info:
        provider._request(mock_session, "SZ000001")
    assert exc_info.value.kind == "auth", f"Expected 'auth', got '{exc_info.value.kind}'"


def test_xueqiu_403_is_auth_error():
    """HTTP 403 应归类为 auth 错误"""
    mock_session = MagicMock(spec=requests.Session)
    response = MagicMock()
    response.status_code = 403
    response.raise_for_status.side_effect = requests.HTTPError(response=response)
    mock_session.get.return_value = response

    provider = XueqiuRealtimeQuote()
    with pytest.raises(DataFetchError) as exc_info:
        provider._request(mock_session, "SZ000001")
    assert exc_info.value.kind == "auth", f"Expected 'auth', got '{exc_info.value.kind}'"
