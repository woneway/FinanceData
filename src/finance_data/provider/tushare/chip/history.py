"""筹码分布 - tushare 实现"""
from finance_data.interface.chip.history import ChipDistribution
from finance_data.interface.types import DataResult, DataFetchError
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _ts_code(symbol: str) -> str:
    if "." in symbol:
        return symbol
    return f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"


class TushareChipHistory:
    def get_chip_distribution_history(self, symbol: str) -> DataResult:
        pro = get_pro()
        ts_code = _ts_code(symbol)
        try:
            df = pro.cyq_perf(
                ts_code=ts_code,
                fields="ts_code,trade_date,weight_avg,winner_rate,cost_5pct,cost_95pct",
            )
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "cyq_perf", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "cyq_perf", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "cyq_perf", f"无数据: {symbol}", "data")

        rows = [ChipDistribution(
            symbol=symbol,
            date=str(r.get("trade_date", "")).replace("-", ""),
            avg_cost=float(r.get("weight_avg", 0) or 0),
            concentration=None,
            profit_ratio=float(r.get("winner_rate", 0) or 0),
            cost_90=float(r.get("cost_95pct", 0) or 0),
            cost_10=float(r.get("cost_5pct", 0) or 0),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="tushare",
                          meta={"rows": len(rows), "symbol": symbol})
