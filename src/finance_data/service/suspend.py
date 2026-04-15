"""停牌信息 service - 统一对外入口"""
import logging

from finance_data.interface.suspend.history import SuspendProtocol
from finance_data.interface.types import DataFetchError, DataResult

logger = logging.getLogger(__name__)


class _SuspendDispatcher:
    def __init__(self, providers: list[SuspendProtocol]):
        self._providers = providers

    def get_suspend_history(self, date: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_suspend_history(date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_suspend_history", "所有数据源均失败", "data")


def _build_suspend() -> _SuspendDispatcher:
    import os
    from finance_data.provider.akshare.suspend.history import AkshareSuspend
    providers: list[SuspendProtocol] = [AkshareSuspend()]
    if os.getenv("TUSHARE_TOKEN"):
        from finance_data.provider.tushare.suspend.history import TushareSuspend
        providers.append(TushareSuspend())
    return _SuspendDispatcher(providers=providers)


suspend = _build_suspend()
