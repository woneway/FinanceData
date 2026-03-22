"""
股票基础信息接口
数据源: akshare (雪球)
"""
import contextlib
import datetime
import requests
import akshare as ak

from finance_data.provider.models import StockInfo
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


@contextlib.contextmanager
def _no_proxy():
    """临时禁用 requests 代理（含 macOS 系统代理），akshare 国内数据源直连更稳定。"""
    orig_init = requests.Session.__init__

    def _init_no_proxy(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self.trust_env = False

    requests.Session.__init__ = _init_no_proxy
    try:
        yield
    finally:
        requests.Session.__init__ = orig_init


def _to_xq_symbol(symbol: str) -> str:
    """将纯数字代码转换为雪球格式（SZ000001 / SH600519）。"""
    if symbol.startswith(("SH", "SZ")):
        return symbol
    if symbol.startswith("6"):
        return f"SH{symbol}"
    return f"SZ{symbol}"


def _ms_to_date(ms) -> str:
    """Unix 毫秒时间戳转 YYYYMMDD 字符串。"""
    try:
        return datetime.datetime.fromtimestamp(int(ms) / 1000).strftime("%Y%m%d")
    except Exception:
        return str(ms)


def _parse_stock_info(symbol: str, df) -> StockInfo:
    """将雪球 DataFrame 解析为 StockInfo。"""
    rows = {row["item"]: row["value"] for _, row in df.iterrows()}

    industry_raw = rows.get("affiliate_industry") or {}
    industry = industry_raw.get("ind_name", "") if isinstance(industry_raw, dict) else ""

    listed_ms = rows.get("listed_date")
    list_date = _ms_to_date(listed_ms) if listed_ms else ""

    return StockInfo(
        symbol=symbol,
        name=rows.get("org_short_name_cn", ""),
        industry=industry,
        list_date=list_date,
        area=rows.get("provincial_name", ""),
        market="",  # 雪球接口无市场分类字段
    )


def get_stock_info(symbol: str) -> DataResult:
    """
    获取个股基本信息。

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        DataResult，data 为 [StockInfo.to_dict()]

    Raises:
        DataFetchError: 网络错误或数据错误
    """
    xq_symbol = _to_xq_symbol(symbol)

    try:
        with _no_proxy():
            df = ak.stock_individual_basic_info_xq(symbol=xq_symbol)
    except _NETWORK_ERRORS as e:
        raise DataFetchError(
            source="akshare",
            func="stock_individual_basic_info_xq",
            reason=str(e),
            kind="network",
        ) from e
    except Exception as e:
        raise DataFetchError(
            source="akshare",
            func="stock_individual_basic_info_xq",
            reason=str(e),
            kind="data",
        ) from e

    info = _parse_stock_info(symbol, df)
    return DataResult(
        data=[info.to_dict()],
        source="akshare",
        meta={"rows": 1, "symbol": symbol},
    )
