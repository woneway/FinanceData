"""测试浏览器 cookie 自动提取"""
import http.cookiejar
from unittest.mock import MagicMock, patch

import pytest


class TestExtractBrowserCookies:
    """_extract_browser_cookies() 测试"""

    def test_returns_none_when_library_not_installed(self):
        """browser-cookie3 未安装时返回 None"""
        with patch.dict("sys.modules", {"browser_cookie3": None}):
            # 重新导入以触发 ImportError
            from finance_data.provider.xueqiu import client
            # 清除可能缓存的 import
            import importlib
            importlib.reload(client)
            result = client._extract_browser_cookies()
            assert result is None

    def test_returns_cookies_from_chrome(self):
        """Chrome 有 xueqiu cookie 时返回 dict 并缓存"""
        mock_cookie = MagicMock()
        mock_cookie.name = "xq_a_token"
        mock_cookie.value = "test_token_value"
        mock_cookie.domain = ".xueqiu.com"

        mock_browser_cookie3 = MagicMock()
        mock_browser_cookie3.chrome.return_value = [mock_cookie]
        mock_browser_cookie3.chrome.__name__ = "chrome"

        with patch.dict("sys.modules", {"browser_cookie3": mock_browser_cookie3}):
            from finance_data.provider.xueqiu import client
            import importlib
            importlib.reload(client)

            with patch.object(client, "_save_cookie_cache") as mock_save:
                result = client._extract_browser_cookies()

                assert result == {"xq_a_token": "test_token_value"}
                # _save_cookie_cache 不在 _extract_browser_cookies 中调用
                # 而是在 _build_session 中调用

    def test_returns_none_when_no_xueqiu_cookies(self):
        """浏览器无 xueqiu cookie 时返回 None"""
        mock_cookie = MagicMock()
        mock_cookie.name = "other_cookie"
        mock_cookie.value = "value"
        mock_cookie.domain = ".other.com"

        mock_browser_cookie3 = MagicMock()
        mock_browser_cookie3.chrome.return_value = [mock_cookie]
        mock_browser_cookie3.chrome.__name__ = "chrome"
        mock_browser_cookie3.safari.return_value = []
        mock_browser_cookie3.safari.__name__ = "safari"

        with patch.dict("sys.modules", {"browser_cookie3": mock_browser_cookie3}):
            from finance_data.provider.xueqiu import client
            import importlib
            importlib.reload(client)

            result = client._extract_browser_cookies()
            assert result is None

    def test_falls_back_to_safari_when_chrome_fails(self):
        """Chrome 失败时 fallback 到 Safari"""
        mock_cookie = MagicMock()
        mock_cookie.name = "u"
        mock_cookie.value = "user_id"
        mock_cookie.domain = ".xueqiu.com"

        mock_browser_cookie3 = MagicMock()
        mock_browser_cookie3.chrome.side_effect = PermissionError("denied")
        mock_browser_cookie3.chrome.__name__ = "chrome"
        mock_browser_cookie3.safari.return_value = [mock_cookie]
        mock_browser_cookie3.safari.__name__ = "safari"

        with patch.dict("sys.modules", {"browser_cookie3": mock_browser_cookie3}):
            from finance_data.provider.xueqiu import client
            import importlib
            importlib.reload(client)

            result = client._extract_browser_cookies()
            assert result == {"u": "user_id"}


class TestHasLoginCookie:
    """has_login_cookie() 测试"""

    def test_returns_true_with_env_cookie(self):
        """环境变量设置时返回 True"""
        with patch.dict("os.environ", {"XUEQIU_COOKIE": "xq_a_token=abc"}):
            from finance_data.provider.xueqiu import client
            import importlib
            importlib.reload(client)
            assert client.has_login_cookie() is True

    def test_returns_true_with_cached_login_cookie(self):
        """文件缓存有登录 cookie 时返回 True"""
        with patch.dict("os.environ", {}, clear=False):
            # 确保 XUEQIU_COOKIE 不存在
            import os
            os.environ.pop("XUEQIU_COOKIE", None)

            from finance_data.provider.xueqiu import client
            import importlib
            importlib.reload(client)

            with patch.object(
                client, "_load_cached_cookie",
                return_value={"ts": 9999999999, "cookies": {"xq_a_token": "cached"}}
            ):
                with patch.object(client, "_extract_browser_cookies"):
                    assert client.has_login_cookie() is True

    def test_returns_true_with_browser_cookies(self):
        """浏览器有 cookie 时返回 True"""
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("XUEQIU_COOKIE", None)

            from finance_data.provider.xueqiu import client
            import importlib
            importlib.reload(client)

            with patch.object(client, "_load_cached_cookie", return_value=None):
                with patch.object(
                    client, "_extract_browser_cookies",
                    return_value={"xq_a_token": "browser"}
                ):
                    assert client.has_login_cookie() is True

    def test_returns_false_when_no_cookies(self):
        """无任何 cookie 来源时返回 False"""
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("XUEQIU_COOKIE", None)

            from finance_data.provider.xueqiu import client
            import importlib
            importlib.reload(client)

            with patch.object(client, "_load_cached_cookie", return_value=None):
                with patch.object(client, "_extract_browser_cookies", return_value=None):
                    assert client.has_login_cookie() is False


class TestBuildSessionBrowserTier:
    """_build_session() 浏览器 cookie 层测试"""

    def test_browser_cookies_used_before_cache(self):
        """浏览器 cookie 优先于文件缓存和访客 cookie"""
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("XUEQIU_COOKIE", None)

            from finance_data.provider.xueqiu import client
            import importlib
            importlib.reload(client)

            browser_cookies = {"xq_a_token": "from_browser", "u": "12345"}

            with patch.object(
                client, "_extract_browser_cookies", return_value=browser_cookies
            ) as mock_extract:
                with patch.object(client, "_save_cookie_cache") as mock_save:
                    with patch.object(client, "_load_cached_cookie") as mock_cache:
                        with patch.object(client, "_fetch_visitor_cookie") as mock_visitor:
                            session = client._build_session()

                            mock_extract.assert_called_once()
                            mock_save.assert_called_once_with(browser_cookies)
                            # 缓存和访客 cookie 不应被调用
                            mock_cache.assert_not_called()
                            mock_visitor.assert_not_called()

                            assert session.cookies.get("xq_a_token") == "from_browser"
                            assert session.cookies.get("u") == "12345"

    def test_falls_through_to_cache_when_no_browser_cookies(self):
        """浏览器无 cookie 时 fallback 到文件缓存"""
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("XUEQIU_COOKIE", None)

            from finance_data.provider.xueqiu import client
            import importlib
            importlib.reload(client)

            with patch.object(client, "_extract_browser_cookies", return_value=None):
                with patch.object(
                    client, "_load_cached_cookie",
                    return_value={"ts": 9999999999, "cookies": {"xq_a_token": "cached_val"}}
                ):
                    with patch.object(client, "_fetch_visitor_cookie") as mock_visitor:
                        session = client._build_session()

                        mock_visitor.assert_not_called()
                        assert session.cookies.get("xq_a_token") == "cached_val"
