"""市场统计 - tushare 无直接接口"""
from finance_data.provider.types import DataResult, DataFetchError


def get_market_stats() -> DataResult:
    raise DataFetchError("tushare", "get_market_stats",
                         "tushare 无直接市场统计接口", "data")
