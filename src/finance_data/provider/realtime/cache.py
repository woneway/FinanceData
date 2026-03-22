from cachetools import TTLCache

# 实时行情缓存：最多 512 支股票，20 分钟 TTL
_quote_cache: TTLCache = TTLCache(maxsize=512, ttl=1200)


def get_cached(key: str):
    return _quote_cache.get(key)


def set_cached(key: str, value) -> None:
    _quote_cache[key] = value
