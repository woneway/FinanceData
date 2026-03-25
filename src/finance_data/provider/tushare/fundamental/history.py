"""财务基本面 - tushare 实现"""
from finance_data.interface.fundamental.history import FinancialSummary, DividendRecord
from finance_data.interface.types import DataResult, DataFetchError
from finance_data.provider.tushare.client import get_pro

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _ts_code(symbol: str) -> str:
    if "." in symbol:
        return symbol
    return f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"


def _opt(val):
    try:
        v = float(val)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


class TushareFinancialSummary:
    def get_financial_summary_history(self, symbol: str) -> DataResult:
        pro = get_pro()
        ts_code = _ts_code(symbol)
        try:
            df_income = pro.income(ts_code=ts_code, fields="end_date,total_revenue,n_income")
            df_fina = pro.fina_indicator(ts_code=ts_code,
                                         fields="end_date,roe,grossprofit_margin,n_cashflow_act")
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "income/fina_indicator", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "income/fina_indicator", reason, kind) from e

        if df_income is None or df_income.empty:
            raise DataFetchError("tushare", "income", f"无数据: {symbol}", "data")

        fina_map = {}
        if df_fina is not None and not df_fina.empty:
            for _, r in df_fina.iterrows():
                fina_map[str(r.get("end_date", ""))] = r

        rows = []
        for _, r in df_income.iterrows():
            period = str(r.get("end_date", ""))
            fi = fina_map.get(period)
            rows.append(FinancialSummary(
                symbol=symbol, period=period.replace("-", ""),
                revenue=_opt(r.get("total_revenue")),
                net_profit=_opt(r.get("n_income")),
                roe=_opt(fi.get("roe")) if fi is not None else None,
                gross_margin=_opt(fi.get("grossprofit_margin")) if fi is not None else None,
                cash_flow=_opt(fi.get("n_cashflow_act")) if fi is not None else None,
            ).to_dict())

        return DataResult(data=rows, source="tushare", meta={"rows": len(rows), "symbol": symbol})


class TushareDividend:
    def get_dividend_history(self, symbol: str) -> DataResult:
        pro = get_pro()
        ts_code = _ts_code(symbol)
        try:
            df = pro.dividend(ts_code=ts_code, fields="ex_date,cash_div,record_date")
        except _NETWORK_ERRORS as e:
            raise DataFetchError("tushare", "dividend", str(e), "network") from e
        except Exception as e:
            reason = str(e)
            kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
            raise DataFetchError("tushare", "dividend", reason, kind) from e

        if df is None or df.empty:
            raise DataFetchError("tushare", "dividend", f"无数据: {symbol}", "data")

        rows = [DividendRecord(
            symbol=symbol,
            ex_date=str(r.get("ex_date", "")).replace("-", ""),
            per_share=float(r.get("cash_div", 0) or 0),
            record_date=str(r.get("record_date", "")).replace("-", ""),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="tushare", meta={"rows": len(rows), "symbol": symbol})
