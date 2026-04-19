"""财务基本面 - akshare 实现"""
import contextlib
import requests
import akshare as ak

from finance_data.interface.fundamental.history import (
    FinancialSummary, DividendRecord,
)
from finance_data.interface.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


@contextlib.contextmanager
def _no_proxy():
    orig = requests.Session.__init__

    def _init(self, *a, **kw):
        orig(self, *a, **kw)
        self.trust_env = False

    requests.Session.__init__ = _init
    try:
        yield
    finally:
        requests.Session.__init__ = orig


def _opt(val):
    try:
        v = float(val)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def _recent_quarters(n: int = 5) -> list[str]:
    import datetime
    today = datetime.date.today()
    quarter_ends = [(3, 31), (6, 30), (9, 30), (12, 31)]
    quarters = []
    year = today.year
    while len(quarters) < n:
        for month, day in reversed(quarter_ends):
            d = datetime.date(year, month, day)
            if d <= today + datetime.timedelta(days=45):
                quarters.append(d.strftime("%Y%m%d"))
            if len(quarters) >= n:
                break
        year -= 1
    return quarters


class AkshareFinancialSummary:
    def get_financial_summary_history(
        self, symbol: str, start_date: str = "", end_date: str = "",
    ) -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_financial_abstract(symbol=symbol)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_financial_abstract", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_financial_abstract", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_financial_abstract", f"无数据: {symbol}", "data")

        df_idx = df.drop_duplicates(subset="指标", keep="first").set_index("指标")
        date_cols = [c for c in df_idx.columns if c not in ("选项",)]

        def _row(metric):
            return df_idx.loc[metric] if metric in df_idx.index else None

        rev_row = _row("营业总收入")
        np_row = _row("净利润")
        roe_row = _row("净资产收益率(ROE)")
        gm_row = _row("毛利率")
        cf_row = _row("经营现金流量净额")

        rows = []
        for date_col in date_cols[:20]:
            rows.append(FinancialSummary(
                symbol=symbol, period=str(date_col),
                revenue=_opt(rev_row[date_col] if rev_row is not None else None),
                net_profit=_opt(np_row[date_col] if np_row is not None else None),
                roe=_opt(roe_row[date_col] if roe_row is not None else None),
                gross_margin=_opt(gm_row[date_col] if gm_row is not None else None),
                cash_flow=_opt(cf_row[date_col] if cf_row is not None else None),
            ).to_dict())

        if start_date or end_date:
            rows = [r for r in rows if
                    (not start_date or r.get("period", "") >= start_date) and
                    (not end_date or r.get("period", "") <= end_date)]

        return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "symbol": symbol})


def _parse_per_share_dividend(desc: str) -> float:
    """从分红方案说明中提取每股分红金额，如 '10送3股派5元' → 0.5"""
    import re
    s = str(desc)
    base_m = re.match(r"(\d+)", s)
    cash_m = re.search(r"派([\d.]+)元?", s)
    if base_m and cash_m:
        base = float(base_m.group(1))
        amount = float(cash_m.group(1))
        return round(amount / base, 4) if base > 0 else 0.0
    return 0.0


class AkshareDividend:
    def get_dividend_history(self, symbol: str) -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_fhps_detail_ths(symbol=symbol)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_fhps_detail_ths", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_fhps_detail_ths", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_fhps_detail_ths", f"无数据: {symbol}", "data")

        import pandas as pd
        rows = []
        for _, r in df.iterrows():
            ex_raw = r.get("A股除权除息日")
            if pd.isna(ex_raw):
                continue
            ex_date = str(ex_raw).replace("-", "")
            per_share = _parse_per_share_dividend(r.get("分红方案说明", ""))
            if per_share <= 0:
                continue
            rec_raw = r.get("A股股权登记日")
            record_date = "" if pd.isna(rec_raw) else str(rec_raw).replace("-", "")
            rows.append(DividendRecord(
                symbol=symbol, ex_date=ex_date,
                per_share=per_share, record_date=record_date,
            ).to_dict())

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "symbol": symbol, "upstream": "ths"})
