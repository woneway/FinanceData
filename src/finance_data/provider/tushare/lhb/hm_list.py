"""游资名录 - tushare 实现"""
from finance_data.interface.lhb.hm import HmEntry
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


class TushareHmList:
    def get_hm_list(self) -> DataResult:
        pro = get_pro()
        try:
            df = pro.hm_list()
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "hm_list", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "hm_list", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "hm_list", "无数据", "data")

        rows = [
            HmEntry(
                name=str(row.get("name", "")),
                desc=str(row.get("desc", "") or ""),
                orgs=str(row.get("orgs", "") or ""),
            ).to_dict()
            for _, row in df.iterrows()
        ]
        return DataResult(data=rows, source="tushare", meta={"rows": len(rows)})
