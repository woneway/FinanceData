"""股票池 - tushare（无等价接口，统一 raise）"""
from finance_data.provider.types import DataFetchError


def get_zt_pool(date: str):
    raise DataFetchError("tushare", "get_zt_pool", "tushare 不支持此接口", "data")


def get_strong_stocks(date: str):
    raise DataFetchError("tushare", "get_strong_stocks", "tushare 不支持此接口", "data")


def get_previous_zt(date: str):
    raise DataFetchError("tushare", "get_previous_zt", "tushare 不支持此接口", "data")


def get_zbgc_pool(date: str):
    raise DataFetchError("tushare", "get_zbgc_pool", "tushare 不支持此接口", "data")
