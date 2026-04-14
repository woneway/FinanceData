"""北向资金 - tushare 实现"""
from finance_data.interface.north_flow.history import NorthStockHold
from finance_data.interface.types import DataResult, DataFetchError
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)

_MARKET_TO_EXCHANGE = {"沪股通": "SH", "深股通": "SZ"}


class TushareNorthStockHold:
    def get_north_stock_hold_history(
        self,
        symbol: str = "",
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
        exchange: str = "",
    ) -> DataResult:
        pro = get_pro()
        kwargs: dict = {}
        if symbol:
            kwargs["ts_code"] = symbol
        if trade_date:
            kwargs["trade_date"] = trade_date
        if start_date:
            kwargs["start_date"] = start_date
        if end_date:
            kwargs["end_date"] = end_date
        if exchange:
            kwargs["exchange"] = _MARKET_TO_EXCHANGE.get(exchange, exchange)
        try:
            df = pro.hk_hold(**kwargs)
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
                hold_volume=float(row.get("vol", 0) or 0),
                hold_ratio=float(row.get("ratio", 0) or 0),
                exchange=str(row.get("exchange", "") or ""),
            ).to_dict())

        return DataResult(data=rows, source="tushare",
                          meta={"rows": len(rows), "symbol": symbol, "trade_date": trade_date})
