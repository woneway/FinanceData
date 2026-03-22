"""行业板块排名 - tushare 暂无对应接口，此文件保留结构但抛出 data 错误"""
from finance_data.provider.types import DataResult, DataFetchError


def get_sector_rank() -> DataResult:
    raise DataFetchError("tushare", "get_sector_rank",
                         "tushare 无行业板块排名接口", "data")
