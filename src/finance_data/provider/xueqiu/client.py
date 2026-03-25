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

    # 优先使用环境变量注入的登录 cookie
    env_cookie = os.environ.get("XUEQIU_COOKIE", "")
    if env_cookie:
        for item in env_cookie.split(";"):
            item = item.strip()
            if "=" in item:
                k, v = item.split("=", 1)
                s.cookies.set(k.strip(), v.strip())
        return s

    # 尝试加载文件缓存
    cached = _load_cached_cookie()
    if cached and cached.get("cookies"):
        for k, v in cached["cookies"].items():
            s.cookies.set(k, v)
        return s

    # 获取访客 cookie
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
    """检查是否配置了登录 cookie（K线等需要认证的接口使用）"""
    return bool(os.environ.get("XUEQIU_COOKIE", ""))
