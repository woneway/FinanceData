"""日频基本面 service - 统一对外入口

数据源优先级：tencent（实时65ms）
"""
import logging

from finance_data.interface.daily_basic.history import DailyBasicProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tencent.daily_basic import TencentDailyBasic

logger = logging.getLogger(__name__)


class _DailyBasicDispatcher:
    def __init__(self, providers: list[DailyBasicProtocol]):
        self._providers = providers

    def get_daily_basic(self, symbol: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_daily_basic(symbol)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_daily_basic", "所有数据源均失败", "data")


daily_basic = _DailyBasicDispatcher(providers=[TencentDailyBasic()])


# --- 全市场按日期查询 ---


def _fill_volume_ratio_from_factor(result: DataResult, trade_date: str) -> DataResult:
    """daily_basic 的 volume_ratio 全缺失时，从 stk_factor_pro 补充。"""
    rows = result.data
    has_vr = any(
        r.get("volume_ratio") is not None and r["volume_ratio"] != 0.0
        for r in rows
    )
    if has_vr:
        return result

    try:
        from finance_data.service.technical import stock_factor
        factor_result = stock_factor.get_stock_factor(trade_date=trade_date)
        vr_map = {
            r["symbol"]: r["volume_ratio"]
            for r in factor_result.data
            if r.get("volume_ratio") is not None and r["volume_ratio"] != 0.0
        }
    except Exception as e:
        logger.warning("stk_factor_pro fallback 获取 volume_ratio 失败: %s", e)
        return result

    if not vr_map:
        return result

    filled = 0
    new_rows = []
    for r in rows:
        sym = r.get("symbol", "").split(".")[0]
        vr = vr_map.get(sym)
        if vr is not None and (r.get("volume_ratio") is None or r["volume_ratio"] == 0.0):
            new_rows.append({**r, "volume_ratio": vr})
            filled += 1
        else:
            new_rows.append(r)

    logger.info("volume_ratio fallback: 从 stk_factor_pro 补充 %d/%d 只", filled, len(rows))
    return DataResult(data=new_rows, source=result.source, meta=result.meta)


class _DailyBasicMarketDispatcher:
    def __init__(self, providers: list):
        self._providers = providers

    def get_daily_basic_market(self, trade_date: str) -> DataResult:
        for p in self._providers:
            try:
                result = p.get_daily_basic_market(trade_date)
                return _fill_volume_ratio_from_factor(result, trade_date)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_daily_basic_market", "所有数据源均失败", "data")


def _build_daily_basic_market() -> _DailyBasicMarketDispatcher:
    from finance_data.provider.tushare.daily_basic.history import TushareDailyBasicMarket
    return _DailyBasicMarketDispatcher(providers=[TushareDailyBasicMarket()])


daily_basic_market = _build_daily_basic_market()
