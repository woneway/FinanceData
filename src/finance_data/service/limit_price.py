"""涨跌停价格 service - 统一对外入口

数据源：tencent（腾讯实时行情 API）
"""
import logging

from finance_data.interface.limit_price.history import LimitPriceProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tencent.limit_price import TencentLimitPrice

logger = logging.getLogger(__name__)


class _LimitPriceDispatcher:
    def __init__(self, providers: list[LimitPriceProtocol]):
        self._providers = providers

    def get_limit_price(self, symbol: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_limit_price(symbol)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_limit_price", "所有数据源均失败", "data")


limit_price = _LimitPriceDispatcher(providers=[TencentLimitPrice()])
