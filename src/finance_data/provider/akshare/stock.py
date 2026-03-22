"""
股票基础信息接口
数据源: akshare
"""
import akshare as ak
from pydantic import BaseModel, Field

from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


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
