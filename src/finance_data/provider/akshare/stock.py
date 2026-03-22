"""
股票基础信息接口
数据源: akshare
"""
import contextlib
import requests
import akshare as ak
from pydantic import BaseModel, Field

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


class StockInfoInput(BaseModel):
    symbol: str = Field(description="股票代码", examples=["000001"])


def get_stock_info(symbol: str) -> DataResult:
    """
    获取个股基本信息。

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        DataResult，data 为 [{"item": str, "value": str}, ...]

    Raises:
        DataFetchError: 网络错误或数据错误
    """
    try:
        with _no_proxy():
            df = ak.stock_individual_info_em(symbol=symbol)
    except _NETWORK_ERRORS as e:
        raise DataFetchError(
            source="akshare",
            func="stock_individual_info_em",
            reason=str(e),
            kind="network",
        ) from e
    except Exception as e:
        raise DataFetchError(
            source="akshare",
            func="stock_individual_info_em",
            reason=str(e),
            kind="data",
        ) from e

    records = df.to_dict(orient="records")

    return DataResult(
        data=records,
        source="akshare",
        meta={"rows": len(records), "symbol": symbol},
    )
