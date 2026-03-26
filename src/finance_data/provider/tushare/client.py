"""tushare pro API 客户端初始化（共享）"""
import logging
import os
import time

import tushare as ts

from finance_data.interface.types import DataFetchError

logger = logging.getLogger(__name__)

# Cached token validation result: (timestamp, is_valid)
_token_valid_cache: tuple[float, bool] | None = None
_TOKEN_CACHE_TTL = 600  # 10 minutes


def get_pro():
    """初始化 tushare pro API，token 和 API URL 从环境变量读取。"""
    token = os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        raise DataFetchError(
            source="tushare",
            func="init",
            reason="TUSHARE_TOKEN 环境变量未设置",
            kind="auth",
        )
    pro = ts.pro_api(token=token)
    api_url = os.environ.get("TUSHARE_API_URL", "")
    if api_url:
        pro._DataApi__token = token
        pro._DataApi__http_url = api_url
    return pro


def is_token_valid() -> bool:
    """Check if TUSHARE_TOKEN is set and actually works (cached for 10min)."""
    global _token_valid_cache

    token = os.environ.get("TUSHARE_TOKEN", "")
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
