"""项目配置加载 — 唯一事实来源为项目根目录 config.toml"""
import tomllib
from functools import lru_cache
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "config.toml"


@lru_cache(maxsize=1)
def _load() -> dict:
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"配置文件不存在: {_CONFIG_PATH}\n"
            "请复制 config.toml.example 为 config.toml 并填写配置"
        )
    with open(_CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def get_tushare_token() -> str:
    return _load()["tushare"]["token"]


def get_tushare_api_url() -> str:
    return _load()["tushare"]["api_url"]


def get_xueqiu_cookie() -> str:
    return _load().get("xueqiu", {}).get("cookie", "")


def has_tushare_token() -> bool:
    """config.toml 中 tushare.token 是否已配置（非空）"""
    try:
        return bool(get_tushare_token())
    except (FileNotFoundError, KeyError):
        return False


def has_tushare_stock_minute_permission() -> bool:
    """config.toml 中 tushare.stock_minute_permission 是否开启"""
    try:
        return bool(_load().get("tushare", {}).get("stock_minute_permission", False))
    except (FileNotFoundError, KeyError):
        return False


def is_cache_enabled() -> bool:
    """config.toml 中 cache.enabled 是否开启（缺省 True，与历史 FINANCE_DATA_CACHE=1 等价）"""
    try:
        return bool(_load().get("cache", {}).get("enabled", True))
    except (FileNotFoundError, KeyError):
        return True


def get_no_proxy_hosts() -> list[str]:
    """config.toml 中 proxy.no_proxy_hosts 列表（缺省含东财域名）"""
    default = ["eastmoney.com", ".eastmoney.com"]
    try:
        hosts = _load().get("proxy", {}).get("no_proxy_hosts", default)
        return list(hosts) if hosts else default
    except (FileNotFoundError, KeyError):
        return default
