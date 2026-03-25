"""雪球 API 客户端 - 共享 session + cookie 管理"""
import json
import logging
import os
import time
from pathlib import Path
from threading import Lock

import requests

from finance_data.interface.types import DataFetchError

logger = logging.getLogger(__name__)

_XUEQIU_HOME = "https://xueqiu.com"
_COOKIE_DIR = Path.home() / ".finance_data"
_COOKIE_FILE = _COOKIE_DIR / "xueqiu_cookie.json"
_COOKIE_TTL = 24 * 3600  # 24 小时

_session: requests.Session | None = None
_session_lock = Lock()
_cookie_ts: float = 0.0


def _to_xueqiu_symbol(symbol: str) -> str:
    """将 A 股代码转为雪球格式：000001 → SZ000001，600519 → SH600519"""
    if symbol.startswith(("SH", "SZ", "sh", "sz")):
        return symbol.upper()
    if symbol.startswith("6"):
        return f"SH{symbol}"
    return f"SZ{symbol}"


def _load_cached_cookie() -> dict | None:
    """从文件加载缓存的 cookie"""
    try:
        if _COOKIE_FILE.exists():
            data = json.loads(_COOKIE_FILE.read_text(encoding="utf-8"))
            if time.time() - data.get("ts", 0) < _COOKIE_TTL:
                return data
    except (json.JSONDecodeError, OSError) as e:
        logger.debug("读取 cookie 缓存失败: %s", e)
    return None


def _save_cookie_cache(cookies: dict[str, str]) -> None:
    """将 cookie 持久化到文件"""
    try:
        _COOKIE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {"ts": time.time(), "cookies": cookies}
        _COOKIE_FILE.write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as e:
        logger.debug("保存 cookie 缓存失败: %s", e)


def _fetch_visitor_cookie(session: requests.Session) -> None:
    """访问雪球首页获取访客 cookie"""
    try:
        resp = session.get(_XUEQIU_HOME, timeout=10)
        resp.raise_for_status()
        cookie_dict = dict(session.cookies)
        _save_cookie_cache(cookie_dict)
    except (requests.RequestException, OSError) as e:
        logger.warning("获取雪球访客 cookie 失败: %s", e)


def _find_chrome_cookie_files() -> list[Path]:
    """查找所有 Chrome Profile 的 Cookies 文件"""
    chrome_dir = Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    if not chrome_dir.exists():
        return []
    cookie_files = sorted(chrome_dir.glob("*/Cookies"))
    return cookie_files


def _extract_browser_cookies() -> dict[str, str] | None:
    """尝试从浏览器提取雪球登录 cookie（Chrome 所有 Profile → Safari）"""
    try:
        import browser_cookie3
    except ImportError:
        logger.debug("browser-cookie3 未安装，跳过浏览器 cookie 提取")
        return None

    # Chrome: 扫描所有 Profile
    for cookie_file in _find_chrome_cookie_files():
        try:
            cj = browser_cookie3.chrome(
                cookie_file=str(cookie_file), domain_name=".xueqiu.com"
            )
            cookies = {c.name: c.value for c in cj if "xueqiu" in c.domain}
            if cookies and any(k.startswith("xq_") or k == "u" for k in cookies):
                logger.info(
                    "从 Chrome(%s) 提取到 %d 个雪球 cookie",
                    cookie_file.parent.name, len(cookies),
                )
                return cookies
        except Exception as e:
            logger.debug("从 Chrome(%s) 提取 cookie 失败: %s", cookie_file.parent.name, e)

    # Safari fallback
    try:
        cj = browser_cookie3.safari(domain_name=".xueqiu.com")
        cookies = {c.name: c.value for c in cj if "xueqiu" in c.domain}
        if cookies and any(k.startswith("xq_") or k == "u" for k in cookies):
            logger.info("从 Safari 提取到 %d 个雪球 cookie", len(cookies))
            return cookies
    except Exception as e:
        logger.debug("从 Safari 提取 cookie 失败: %s", e)

    return None


def _build_session() -> requests.Session:
    """创建并初始化 session"""
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://xueqiu.com/",
    })

    # Tier 1: 环境变量
    env_cookie = os.environ.get("XUEQIU_COOKIE", "")
    if env_cookie:
        for item in env_cookie.split(";"):
            item = item.strip()
            if "=" in item:
                k, v = item.split("=", 1)
                s.cookies.set(k.strip(), v.strip())
        return s

    # Tier 2: 浏览器自动提取
    browser_cookies = _extract_browser_cookies()
    if browser_cookies:
        for k, v in browser_cookies.items():
            s.cookies.set(k, v)
        _save_cookie_cache(browser_cookies)
        return s

    # Tier 3: 文件缓存
    cached = _load_cached_cookie()
    if cached and cached.get("cookies"):
        for k, v in cached["cookies"].items():
            s.cookies.set(k, v)
        return s

    # Tier 4: 访客 cookie
    _fetch_visitor_cookie(s)
    return s


def get_session() -> requests.Session:
    """获取共享 session（线程安全单例）"""
    global _session, _cookie_ts
    with _session_lock:
        now = time.time()
        if _session is None or (now - _cookie_ts > _COOKIE_TTL):
            _session = _build_session()
            _cookie_ts = now
        return _session


def refresh_session() -> requests.Session:
    """强制刷新 session（cookie 过期时调用）"""
    global _session, _cookie_ts
    with _session_lock:
        _session = _build_session()
        _cookie_ts = time.time()
        return _session


def has_login_cookie() -> bool:
    """检查是否有登录 cookie（env / 文件缓存 / 浏览器提取）"""
    if os.environ.get("XUEQIU_COOKIE", ""):
        return True
    cached = _load_cached_cookie()
    if cached and cached.get("cookies"):
        cookies = cached["cookies"]
        if any(k.startswith("xq_") or k == "u" for k in cookies):
            return True
    if _extract_browser_cookies():
        return True
    return False
