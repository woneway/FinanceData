"""股票技术面因子专业版 - tushare provider"""
import math

from finance_data.interface.technical.factor import StockFactor
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _safe(val: object, default: float = 0.0) -> float:
    try:
        v = float(val)  # type: ignore[arg-type]
        return default if math.isnan(v) else v
    except (TypeError, ValueError):
        return default


class TushareStockFactor:
    def get_stock_factor(
        self,
        ts_code: str = "",
        trade_date: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> DataResult:
        pro = get_pro()
        params: dict = {}
        if ts_code:
            params["ts_code"] = ts_code
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        try:
            df = pro.stk_factor_pro(**params)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "stk_factor_pro", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "stk_factor_pro", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError(
                "tushare", "stk_factor_pro",
                f"无数据: ts_code={ts_code}, trade_date={trade_date}", "data",
            )

        rows = []
        for _, r in df.iterrows():
            symbol = str(r.get("ts_code", "")).split(".")[0]
            # 单位转换：vol 手→股(×100), amount 千元→元(×1000)
            # total_mv/circ_mv 万元→元(×10000), *_share 万股→股(×10000)
            rows.append(StockFactor(
                trade_date=str(r.get("trade_date", "")),
                symbol=symbol,
                close=_safe(r.get("close")),
                open=_safe(r.get("open")),
                high=_safe(r.get("high")),
                low=_safe(r.get("low")),
                pre_close=_safe(r.get("pre_close")),
                change=_safe(r.get("change")),
                pct_chg=_safe(r.get("pct_chg")),
                volume=_safe(r.get("vol")) * 100,
                amount=_safe(r.get("amount")) * 1000,
                turnover_rate=_safe(r.get("turnover_rate")),
                turnover_rate_f=_safe(r.get("turnover_rate_f")),
                volume_ratio=_safe(r.get("volume_ratio")),
                pe=_safe(r.get("pe")),
                pe_ttm=_safe(r.get("pe_ttm")),
                pb=_safe(r.get("pb")),
                ps=_safe(r.get("ps")),
                ps_ttm=_safe(r.get("ps_ttm")),
                total_share=_safe(r.get("total_share")) * 10000,
                float_share=_safe(r.get("float_share")) * 10000,
                free_share=_safe(r.get("free_share")) * 10000,
                total_mv=_safe(r.get("total_mv")) * 10000,
                circ_mv=_safe(r.get("circ_mv")) * 10000,
                dv_ratio=_safe(r.get("dv_ratio")),
                dv_ttm=_safe(r.get("dv_ttm")),
                free_mv=_safe(r.get("free_mv")) * 10000 if r.get("free_mv") is not None else 0.0,
                ma5=_safe(r.get("ma_bfq_5")),
                ma10=_safe(r.get("ma_bfq_10")),
                ma20=_safe(r.get("ma_bfq_20")),
                ma30=_safe(r.get("ma_bfq_30")),
                ma60=_safe(r.get("ma_bfq_60")),
                ma90=_safe(r.get("ma_bfq_90")),
                ma250=_safe(r.get("ma_bfq_250")),
                macd_dif=_safe(r.get("macd_dif_bfq")),
                macd_dea=_safe(r.get("macd_dea_bfq")),
                macd=_safe(r.get("macd_bfq")),
                kdj_k=_safe(r.get("kdj_k_bfq")),
                kdj_d=_safe(r.get("kdj_d_bfq")),
                kdj_j=_safe(r.get("kdj_bfq")),
                rsi_6=_safe(r.get("rsi_bfq_6")),
                rsi_12=_safe(r.get("rsi_bfq_12")),
                rsi_24=_safe(r.get("rsi_bfq_24")),
                boll_upper=_safe(r.get("boll_upper_bfq")),
                boll_mid=_safe(r.get("boll_mid_bfq")),
                boll_lower=_safe(r.get("boll_lower_bfq")),
                cci=_safe(r.get("cci_bfq")),
            ).to_dict())

        return DataResult(
            data=rows,
            source="tushare",
            meta={"rows": len(rows), "ts_code": ts_code, "trade_date": trade_date},
        )
