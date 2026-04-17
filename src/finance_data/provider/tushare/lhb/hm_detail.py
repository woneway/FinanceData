"""游资每日交易明细 - tushare 实现"""
from finance_data.interface.lhb.hm import HmDetailEntry
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.cache.resolver import resolve
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _flt(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if v != v else v
    except (TypeError, ValueError):
        return default


class TushareHmDetail:
    def get_hm_detail(
        self, trade_date: str = "", start_date: str = "", end_date: str = "",
        hm_name: str = "",
    ) -> DataResult:
        pro = get_pro()
        kwargs: dict[str, str] = {}
        if trade_date:
            kwargs["trade_date"] = trade_date
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date
        if hm_name:
            kwargs["hm_name"] = hm_name
        try:
            extra = f"hm_name = '{hm_name}'" if hm_name else ""
            df = resolve("hm_detail", trade_date, start_date, end_date, extra_where=extra)
            if df is None:
                df = pro.hm_detail(**kwargs)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "hm_detail", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "hm_detail", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "hm_detail", "无数据", "data")

        rows = [
            HmDetailEntry(
                trade_date=str(row.get("trade_date", "")),
                symbol=str(row.get("ts_code", "")),
                name=str(row.get("ts_name", "")),
                buy_amount=_flt(row.get("buy_amount")),
                sell_amount=_flt(row.get("sell_amount")),
                net_amount=_flt(row.get("net_amount")),
                hm_name=str(row.get("hm_name", "")),
                hm_orgs=str(row.get("hm_orgs", "") or ""),
            ).to_dict()
            for _, row in df.iterrows()
        ]
        return DataResult(data=rows, source="tushare", meta={"rows": len(rows)})
