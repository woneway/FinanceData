"""大盘资金流向 - tushare provider"""
from finance_data.interface.fund_flow.market import MarketMoneyflowRow
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


class TushareMarketMoneyflow:
    def get_market_moneyflow(
        self,
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> DataResult:
        pro = get_pro()
        params: dict = {}
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        try:
            df = pro.moneyflow_mkt_dc(**params)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "moneyflow_mkt_dc", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "moneyflow_mkt_dc", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError(
                "tushare", "moneyflow_mkt_dc",
                f"无数据: trade_date={trade_date}", "data",
            )

        def _safe(val: object, default: float = 0.0) -> float:
            try:
                v = float(val)  # type: ignore[arg-type]
                import math
                return 0.0 if math.isnan(v) else v
            except (TypeError, ValueError):
                return default

        rows = []
        for _, r in df.iterrows():
            rows.append(MarketMoneyflowRow(
                trade_date=str(r.get("trade_date", "")),
                close_sh=_safe(r.get("close_sh")),
                pct_change_sh=_safe(r.get("pct_change_sh")),
                close_sz=_safe(r.get("close_sz")),
                pct_change_sz=_safe(r.get("pct_change_sz")),
                net_amount=_safe(r.get("net_amount")),
                net_amount_rate=_safe(r.get("net_amount_rate")),
                buy_lg_amount=_safe(r.get("buy_lg_amount")),
                buy_lg_amount_rate=_safe(r.get("buy_lg_amount_rate")),
                buy_md_amount=_safe(r.get("buy_md_amount")),
                buy_md_amount_rate=_safe(r.get("buy_md_amount_rate")),
                buy_sm_amount=_safe(r.get("buy_sm_amount")),
                buy_sm_amount_rate=_safe(r.get("buy_sm_amount_rate")),
                buy_elg_amount=_safe(r.get("buy_elg_amount")),
                buy_elg_amount_rate=_safe(r.get("buy_elg_amount_rate")),
            ).to_dict())

        return DataResult(
            data=rows,
            source="tushare",
            meta={"rows": len(rows), "trade_date": trade_date},
        )
