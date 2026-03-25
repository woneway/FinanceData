"""北向资金 - tushare 实现"""
from finance_data.interface.north_flow.history import NorthStockHold
from finance_data.interface.types import DataResult, DataFetchError
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


class TushareNorthStockHold:
    def get_north_stock_hold_history(
        self,
        market: str = "沪股通",
        indicator: str = "5日排行",
        symbol: str = "",
        trade_date: str = "",
    ) -> DataResult:
        pro = get_pro()
        try:
            df = pro.hk_hold(
                ts_code=symbol,
                trade_date=trade_date,
            )
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "hk_hold", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "hk_hold", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "hk_hold",
                                 f"无数据: symbol={symbol} trade_date={trade_date}", "data")

        rows = []
        for _, row in df.iterrows():
            ts_code = str(row.get("ts_code", ""))
            sym = ts_code.split(".")[0] if "." in ts_code else ts_code
            rows.append(NorthStockHold(
                symbol=sym,
                name=str(row.get("name", "") or ""),
                date=str(row.get("trade_date", "")).replace("-", ""),
                close_price=0,
                pct_change=0,
                hold_volume=float(row.get("vol", 0) or 0),
                hold_market_cap=0,
                hold_float_ratio=float(row.get("ratio", 0) or 0),
                hold_total_ratio=0,
            ).to_dict())

        return DataResult(data=rows, source="tushare",
                          meta={"rows": len(rows), "symbol": symbol, "trade_date": trade_date})
