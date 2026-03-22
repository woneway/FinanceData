"""资金流向 - tushare 无直接接口"""
from finance_data.provider.types import DataResult, DataFetchError


def get_fund_flow(symbol: str, **kwargs) -> DataResult:
    raise DataFetchError("tushare", "get_fund_flow",
                         "tushare 无个股资金流向接口", "data")
