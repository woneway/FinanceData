"""同花顺热股排行 - tushare 实现"""
import datetime

from finance_data.interface.hot_rank.ths_hot import ThsHotEntry
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _flt(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if v != v else v
    except (TypeError, ValueError):
        return default


def _opt_flt(val):
    try:
        v = float(val)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def _classify_error(exc: Exception) -> DataFetchError:
    reason = str(exc)
    kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
    return DataFetchError("tushare", "ths_hot", reason, kind)


class TushareThsHot:
    def get_ths_hot(self, trade_date: str = "") -> DataResult:
        pro = get_pro()
        kwargs: dict[str, str] = {}
        if trade_date:
            kwargs["trade_date"] = trade_date
        try:
            df = pro.ths_hot(**kwargs)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "ths_hot", str(e), "network") from e
        except Exception as e:
            raise _classify_error(e) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "ths_hot", "无数据", "data")

        # 只保留"热股"类型
        df = df[df["data_type"] == "热股"]
        if df.empty:
            raise DataFetchError("tushare", "ths_hot", "无热股数据", "data")

        # 每只股票取最新 rank_time 去重
        df = df.sort_values("rank_time", ascending=False)
        df = df.drop_duplicates(subset=["ts_code"], keep="first")
        df = df.sort_values("rank", ascending=True)

        rows = [
            ThsHotEntry(
                symbol=str(row.get("ts_code", "")),
                name=str(row.get("ts_name", "")),
                rank=int(row.get("rank", 0)),
                pct_chg=_flt(row.get("pct_change")),
                current_price=_flt(row.get("current_price")),
                hot=_opt_flt(row.get("hot")),
                concept=str(row.get("concept", "") or ""),
                rank_reason=str(row.get("rank_reason", "") or ""),
                trade_date=str(row.get("trade_date", "")),
            ).to_dict()
            for _, row in df.iterrows()
        ]
        return DataResult(
            data=rows,
            source="tushare",
            meta={"rows": len(rows)},
        )
