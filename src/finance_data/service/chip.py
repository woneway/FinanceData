"""筹码分布 service - 统一对外入口"""
import logging
import os

from finance_data.interface.chip.history import ChipHistoryProtocol
from finance_data.interface.types import DataFetchError, DataResult

logger = logging.getLogger(__name__)


class _ChipHistoryDispatcher:
    def __init__(self, providers: list[ChipHistoryProtocol]):
        self._providers = providers

    def get_chip_distribution_history(self, symbol: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_chip_distribution_history(symbol)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_chip_distribution_history", "所有数据源均失败", "data")


def _build_chip_history() -> _ChipHistoryDispatcher:
    # akshare 筹码分布已禁用（依赖东财 stock_cyq_em）
    providers: list[ChipHistoryProtocol] = []
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.chip.history import TushareChipHistory
        providers.append(TushareChipHistory())
    return _ChipHistoryDispatcher(providers=providers)


chip_history = _build_chip_history()
