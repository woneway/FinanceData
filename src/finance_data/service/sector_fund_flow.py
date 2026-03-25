"""板块资金流 service - 统一对外入口（仅 akshare）"""
import logging

from finance_data.interface.sector_fund_flow.history import SectorCapitalFlowProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.sector_fund_flow.history import AkshareSectorCapitalFlow

logger = logging.getLogger(__name__)


class _SectorCapitalFlowDispatcher:
    def __init__(self, providers: list[SectorCapitalFlowProtocol]):
        self._providers = providers

    def get_sector_capital_flow_history(self, indicator: str, sector_type: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_sector_capital_flow_history(indicator, sector_type)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_sector_capital_flow_history", "所有数据源均失败", "data")


sector_capital_flow = _SectorCapitalFlowDispatcher(providers=[AkshareSectorCapitalFlow()])
