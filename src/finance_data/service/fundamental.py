"""财务基本面 service - 统一对外入口"""
import logging
import os

from finance_data.interface.fundamental.history import (
    FinancialSummaryProtocol, DividendProtocol, EarningsForecastProtocol
)
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.fundamental.history import (
    AkshareFinancialSummary, AkshareDividend, AkshareEarningsForecast
)

logger = logging.getLogger(__name__)


class _FinancialSummaryDispatcher:
    def __init__(self, providers: list[FinancialSummaryProtocol]):
        self._providers = providers

    def get_financial_summary_history(self, symbol: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_financial_summary_history(symbol)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_financial_summary_history", "所有数据源均失败", "data")


class _DividendDispatcher:
    def __init__(self, providers: list[DividendProtocol]):
        self._providers = providers

    def get_dividend_history(self, symbol: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_dividend_history(symbol)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_dividend_history", "所有数据源均失败", "data")


class _EarningsForecastDispatcher:
    def __init__(self, providers: list[EarningsForecastProtocol]):
        self._providers = providers

    def get_earnings_forecast_history(self, symbol: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_earnings_forecast_history(symbol)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_earnings_forecast_history", "所有数据源均失败", "data")


def _build_financial_summary() -> _FinancialSummaryDispatcher:
    providers: list[FinancialSummaryProtocol] = [AkshareFinancialSummary()]
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.fundamental.history import TushareFinancialSummary
        providers.append(TushareFinancialSummary())
    return _FinancialSummaryDispatcher(providers=providers)


def _build_dividend() -> _DividendDispatcher:
    providers: list[DividendProtocol] = [AkshareDividend()]
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.fundamental.history import TushareDividend
        providers.append(TushareDividend())
    return _DividendDispatcher(providers=providers)


financial_summary = _build_financial_summary()
dividend = _build_dividend()
earnings_forecast = _EarningsForecastDispatcher(providers=[AkshareEarningsForecast()])
