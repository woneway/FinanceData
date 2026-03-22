from typing import Protocol

from finance_data.provider.models import StockInfo
from finance_data.provider.types import DataResult


class StockProvider(Protocol):
    """个股数据 provider 接口约束：统一入参 symbol，统一出参 DataResult[StockInfo]"""

    def __call__(self, symbol: str) -> DataResult:
        """
        获取个股基本信息。

        Args:
            symbol: 股票代码，如 "000001"

        Returns:
            DataResult，data 为 [StockInfo.to_dict(), ...]

        Raises:
            DataFetchError
        """
        ...
