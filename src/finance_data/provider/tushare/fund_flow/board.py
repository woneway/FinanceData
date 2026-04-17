"""东财概念及行业板块资金流向 - tushare provider"""
import math

from finance_data.interface.fund_flow.board import BoardMoneyflowRow
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.cache.resolver import resolve
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _safe(val: object, default: float = 0.0) -> float:
    try:
        v = float(val)  # type: ignore[arg-type]
        return default if math.isnan(v) else v
    except (TypeError, ValueError):
        return default


class TushareBoardMoneyflow:
    def get_board_moneyflow(
        self,
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
        ts_code: str = "",
        content_type: str = "",
    ) -> DataResult:
        pro = get_pro()
        params: dict = {}
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if ts_code:
            params["ts_code"] = ts_code
        if content_type:
            params["content_type"] = content_type

        try:
            parts = [f"ts_code = '{ts_code}'" if ts_code else "", f"content_type = '{content_type}'" if content_type else ""]
            extra = " AND ".join(p for p in parts if p)
            df = resolve("dc_board_moneyflow", trade_date, start_date, end_date, extra_where=extra)
            if df is None:
                df = pro.moneyflow_ind_dc(**params)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "moneyflow_ind_dc", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "moneyflow_ind_dc", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError(
                "tushare", "moneyflow_ind_dc",
                f"无数据: trade_date={trade_date}", "data",
            )

        rows = []
        for _, r in df.iterrows():
            rows.append(BoardMoneyflowRow(
                trade_date=str(r.get("trade_date", "")),
                ts_code=str(r.get("ts_code", "")),
                name=str(r.get("name", "")),
                content_type=str(r.get("content_type", "")),
                pct_chg=_safe(r.get("pct_change")),
                close=_safe(r.get("close")),
                net_amount=_safe(r.get("net_amount")),
                net_amount_rate=_safe(r.get("net_amount_rate")),
                buy_elg_amount=_safe(r.get("buy_elg_amount")),
                buy_elg_amount_rate=_safe(r.get("buy_elg_amount_rate")),
                buy_lg_amount=_safe(r.get("buy_lg_amount")),
                buy_lg_amount_rate=_safe(r.get("buy_lg_amount_rate")),
                buy_md_amount=_safe(r.get("buy_md_amount")),
                buy_md_amount_rate=_safe(r.get("buy_md_amount_rate")),
                buy_sm_amount=_safe(r.get("buy_sm_amount")),
                buy_sm_amount_rate=_safe(r.get("buy_sm_amount_rate")),
                buy_sm_amount_stock=str(r.get("buy_sm_amount_stock", "")),
                rank=int(_safe(r.get("rank"))),
            ).to_dict())

        return DataResult(
            data=rows,
            source="tushare",
            meta={"rows": len(rows), "trade_date": trade_date},
        )
