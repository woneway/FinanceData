"""雪球客户端测试"""
import json
import time
from unittest.mock import MagicMock, patch

import pytest

from finance_data.provider.xueqiu import client as xueqiu_client
from finance_data.provider.xueqiu.client import (
    _to_xueqiu_symbol,
    get_session,
    has_login_cookie,
    refresh_session,
)


@pytest.fixture(autouse=True)
def _reset_session():
    """每个测试重置全局 session"""
    xueqiu_client._session = None
    xueqiu_client._cookie_ts = 0.0
    yield
    xueqiu_client._session = None
    xueqiu_client._cookie_ts = 0.0


class TestSymbolConversion:
    def test_sz_stock(self):
        # 000xxx → SZ（现有行为兼容）
        assert _to_xueqiu_symbol("000001") == "SZ000001"

    def test_sh_stock(self):
        assert _to_xueqiu_symbol("600519") == "SH600519"

    def test_already_prefixed(self):
        assert _to_xueqiu_symbol("SZ000001") == "SZ000001"
        assert _to_xueqiu_symbol("SH600519") == "SH600519"

    def test_lowercase_prefix(self):
        assert _to_xueqiu_symbol("sz000001") == "SZ000001"


class TestGetSession:
    @patch.dict("os.environ", {"XUEQIU_COOKIE": "xq_a_token=abc123"}, clear=False)
    def test_env_cookie_loaded(self):
        session = get_session()
        assert session.cookies.get("xq_a_token") == "abc123"

    @patch.dict("os.environ", {}, clear=False)
    @patch("finance_data.provider.xueqiu.client._load_cached_cookie", return_value=None)
    @patch("finance_data.provider.xueqiu.client._fetch_visitor_cookie")
    @patch("finance_data.provider.xueqiu.client._extract_browser_cookies", return_value=None)
    def test_visitor_cookie_fetched(self, mock_browser, mock_fetch, mock_cache):
        # 清除 XUEQIU_COOKIE
        import os
        os.environ.pop("XUEQIU_COOKIE", None)
        session = get_session()
        assert session is not None
        mock_fetch.assert_called_once()

    @patch.dict("os.environ", {}, clear=False)
    @patch("finance_data.provider.xueqiu.client._load_cached_cookie")
    @patch("finance_data.provider.xueqiu.client._extract_browser_cookies", return_value=None)
    def test_cached_cookie_used(self, mock_browser, mock_cache):
        import os
        os.environ.pop("XUEQIU_COOKIE", None)
        mock_cache.return_value = {
            "ts": time.time(),
            "cookies": {"xq_a_token": "cached_val"},
        }
        session = get_session()
        assert session.cookies.get("xq_a_token") == "cached_val"


class TestRefreshSession:
    @patch.dict("os.environ", {"XUEQIU_COOKIE": "xq_a_token=new"}, clear=False)
    def test_refresh_creates_new_session(self):
        old = get_session()
        new = refresh_session()
        assert new is not old
        assert new.cookies.get("xq_a_token") == "new"


class TestHasLoginCookie:
    @patch.dict("os.environ", {"XUEQIU_COOKIE": "token=abc"}, clear=False)
    def test_returns_true(self):
        assert has_login_cookie() is True

    @patch.dict("os.environ", {}, clear=False)
    @patch("finance_data.provider.xueqiu.client._extract_browser_cookies", return_value=None)
    @patch("finance_data.provider.xueqiu.client._load_cached_cookie", return_value=None)
    def test_returns_false(self, mock_cache, mock_browser):
        import os
        os.environ.pop("XUEQIU_COOKIE", None)
        assert has_login_cookie() is False


class TestCookieCache:
    def test_save_and_load(self, tmp_path):
        cookie_file = tmp_path / "xueqiu_cookie.json"
        with patch.object(xueqiu_client, "_COOKIE_FILE", cookie_file), \
             patch.object(xueqiu_client, "_COOKIE_DIR", tmp_path):
            xueqiu_client._save_cookie_cache({"xq_a_token": "test"})
            result = xueqiu_client._load_cached_cookie()
        assert result is not None
        assert result["cookies"]["xq_a_token"] == "test"

    def test_expired_cache_returns_none(self, tmp_path):
        cookie_file = tmp_path / "xueqiu_cookie.json"
        expired = {"ts": time.time() - 100000, "cookies": {"xq_a_token": "old"}}
        cookie_file.write_text(json.dumps(expired))
        with patch.object(xueqiu_client, "_COOKIE_FILE", cookie_file):
            result = xueqiu_client._load_cached_cookie()
        assert result is None
