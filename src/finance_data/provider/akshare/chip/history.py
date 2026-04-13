"""筹码分布 - akshare 实现（东财源 stock_cyq_em）"""
import akshare as ak

from finance_data.provider.akshare._proxy import ensure_eastmoney_no_proxy

ensure_eastmoney_no_proxy()

from finance_data.interface.chip.history import ChipDistribution
from finance_data.interface.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


class AkshareChipHistory:
    def get_chip_distribution_history(
        self, symbol: str, start_date: str = "", end_date: str = "",
    ) -> DataResult:
        try:
            df = ak.stock_cyq_em(symbol=symbol, adjust="")
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_cyq_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_cyq_em", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_cyq_em", f"无数据: {symbol}", "data")

        if start_date or end_date:
            df["_date_str"] = df["日期"].astype(str).str.replace("-", "")
            if start_date:
                df = df[df["_date_str"] >= start_date]
            if end_date:
                df = df[df["_date_str"] <= end_date]
            df = df.drop(columns=["_date_str"])

        rows = [ChipDistribution(
            symbol=symbol,
            date=str(r.get("日期", "")).replace("-", ""),
            avg_cost=float(r.get("平均成本", 0) or 0),
            concentration=float(r.get("90集中度", 0) or 0),
            profit_ratio=float(r.get("获利比例", 0) or 0),
            cost_90=float(r.get("90成本-高", 0) or 0),
            cost_10=float(r.get("90成本-低", 0) or 0),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "symbol": symbol})
