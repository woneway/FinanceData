"""财务基本面 - tushare 实现"""
from finance_data.interface.fundamental.history import FinancialSummary, DividendRecord
from finance_data.interface.types import DataResult, DataFetchError
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _ts_code(symbol: str) -> str:
    from finance_data.provider.symbol import to_tushare
    return to_tushare(symbol)


def _opt(val):
    try:
        v = float(val)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


class TushareFinancialSummary:
    def get_financial_summary_history(
        self, symbol: str, start_date: str = "", end_date: str = "",
    ) -> DataResult:
        pro = get_pro()
        ts_code = _ts_code(symbol)
        try:
            df_income = pro.income(ts_code=ts_code, fields="end_date,total_revenue,n_income,report_type")
            df_fina = pro.fina_indicator(ts_code=ts_code,
                                         fields="end_date,roe_waa,grossprofit_margin")
            df_cf = pro.cashflow(ts_code=ts_code, fields="end_date,n_cashflow_act,report_type")
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "income/fina_indicator", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "income/fina_indicator", reason, kind) from e

        if df_income is None or df_income.empty:
            raise DataFetchError("tushare", "income", f"无数据: {symbol}", "data")

        import pandas as pd

        def _latest_by_period(df: pd.DataFrame, limit: int | None = None) -> pd.DataFrame:
            if df is None or df.empty:
                return pd.DataFrame()
            if "report_type" in df.columns:
                report_type = df["report_type"].astype(str)
                filtered = df[report_type.eq("1")]
                if not filtered.empty:
                    df = filtered
            df = df.drop_duplicates(subset="end_date", keep="first")
            df = df.sort_values(by="end_date", ascending=False)
            if limit:
                df = df.head(limit)
            return df

        df_income = _latest_by_period(df_income, limit=20)
        if df_income.empty:
            raise DataFetchError("tushare", "income", f"无有效数据: {symbol}", "data")
        df_fina = _latest_by_period(df_fina)
        df_cf = _latest_by_period(df_cf)

        fina_map: dict[str, object] = {}
        if df_fina is not None and not df_fina.empty:
            for _, r in df_fina.iterrows():
                fina_map[str(r.get("end_date", ""))] = r

        cf_map: dict[str, float | None] = {}
        if df_cf is not None and not df_cf.empty:
            for _, r in df_cf.iterrows():
                cf_map[str(r.get("end_date", ""))] = _opt(r.get("n_cashflow_act"))

        rows = []
        for _, r in df_income.iterrows():
            period = str(r.get("end_date", ""))
            fi = fina_map.get(period)
            rows.append(FinancialSummary(
                symbol=symbol, period=period.replace("-", ""),
                revenue=_opt(r.get("total_revenue")),
                net_profit=_opt(r.get("n_income")),
                roe=_opt(fi.get("roe_waa")) if fi is not None else None,
                gross_margin=_opt(fi.get("grossprofit_margin")) if fi is not None else None,
                cash_flow=cf_map.get(period),
            ).to_dict())

        if start_date or end_date:
            rows = [r for r in rows if
                    (not start_date or r.get("period", "") >= start_date) and
                    (not end_date or r.get("period", "") <= end_date)]

        return DataResult(data=rows, source="tushare", meta={"rows": len(rows), "symbol": symbol})


class TushareDividend:
    def get_dividend_history(self, symbol: str) -> DataResult:
        pro = get_pro()
        ts_code = _ts_code(symbol)
        try:
            df = pro.dividend(ts_code=ts_code, fields="ex_date,cash_div_tax,record_date")
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "dividend", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "dividend", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "dividend", f"无数据: {symbol}", "data")

        import pandas as pd
        rows = []
        for _, r in df.iterrows():
            if pd.isna(r.get("ex_date")):
                continue
            per_share = float(r.get("cash_div_tax", 0) or 0)
            if per_share <= 0:
                continue
            rec_raw = r.get("record_date")
            record_date = "" if pd.isna(rec_raw) else str(rec_raw).replace("-", "")
            rows.append(DividendRecord(
                symbol=symbol,
                ex_date=str(r["ex_date"]).replace("-", ""),
                per_share=per_share,
                record_date=record_date,
            ).to_dict())

        return DataResult(data=rows, source="tushare", meta={"rows": len(rows), "symbol": symbol})
