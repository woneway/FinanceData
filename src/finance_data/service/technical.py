"""股票技术面因子 - 业务编排层"""
import logging
from finance_data.config import has_tushare_token

from finance_data.interface.technical.factor import StockFactorProtocol
from finance_data.interface.types import DataFetchError, DataResult

logger = logging.getLogger(__name__)


class _StockFactorDispatcher:
    def __init__(self, providers: list[StockFactorProtocol]):
        self._providers = providers

    def get_stock_factor(
        self,
        ts_code: str = "",
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> DataResult:
        for p in self._providers:
            try:
                return p.get_stock_factor(ts_code, trade_date, start_date, end_date)
            except DataFetchError as e:
                logger.warning("%s 失败: %s", type(p).__name__, e)
        raise DataFetchError("all", "get_stock_factor", "所有数据源均失败", "data")


def _build_stock_factor() -> _StockFactorDispatcher:
    providers: list[StockFactorProtocol] = []
    if has_tushare_token():
        from finance_data.provider.tushare.technical.factor import TushareStockFactor
        providers.append(TushareStockFactor())
    return _StockFactorDispatcher(providers=providers)


stock_factor = _build_stock_factor()
