"""tushare pro API 客户端初始化（共享）"""
import logging
import time

import tushare as ts

from finance_data.config import get_tushare_api_url, get_tushare_token
from finance_data.interface.types import DataFetchError

logger = logging.getLogger(__name__)

# Cached token validation result: (timestamp, is_valid)
_token_valid_cache: tuple[float, bool] | None = None
_TOKEN_CACHE_TTL = 600  # 10 minutes


def get_pro():
    """初始化 tushare pro API，token 和 API URL 从 config.toml 读取。"""
    token = get_tushare_token()
    if not token:
        raise DataFetchError(
            source="tushare",
            func="init",
            reason="config.toml 中 tushare.token 未设置",
            kind="auth",
        )
    pro = ts.pro_api(token=token)
    api_url = get_tushare_api_url()
    if api_url:
        pro._DataApi__token = token
        pro._DataApi__http_url = api_url
    return pro


def is_token_valid() -> bool:
    """Check if TUSHARE_TOKEN is set and actually works (cached for 10min)."""
    global _token_valid_cache

    try:
        token = get_tushare_token()
    except (FileNotFoundError, KeyError):
        return False
    if not token:
        return False

    now = time.monotonic()
    if _token_valid_cache is not None:
        ts_cached, valid = _token_valid_cache
        if now - ts_cached < _TOKEN_CACHE_TTL:
            return valid

    try:
        pro = get_pro()
        df = pro.trade_cal(exchange="SSE", start_date="20250101", end_date="20250102")
        valid = df is not None and not df.empty
    except Exception as e:
        logger.debug("tushare token validation failed: %s", e)
        valid = False

    _token_valid_cache = (now, valid)
    return valid
