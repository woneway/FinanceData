"""财务基本面 - akshare"""
import contextlib
import requests
import akshare as ak

from finance_data.provider.fundamental.models import (
    FinancialSummary, DividendRecord, EarningsForecast
)
from finance_data.provider.types import DataResult, DataFetchError

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


def get_financial_summary(symbol: str) -> DataResult:
    try:
        with _no_proxy():
            df = ak.stock_financial_abstract(symbol=symbol)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_financial_abstract", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_financial_abstract", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_financial_abstract", f"无数据: {symbol}", "data")

    # akshare 返回宽表：行=指标，列=报告期日期（如 20251231）
    # 需去重后转置，按日期生成每条记录
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
    for date_col in date_cols[:20]:  # 只取最近 20 期
        rows.append(FinancialSummary(
            symbol=symbol,
            period=str(date_col),
            revenue=_opt(rev_row[date_col] if rev_row is not None else None),
            net_profit=_opt(np_row[date_col] if np_row is not None else None),
            roe=_opt(roe_row[date_col] if roe_row is not None else None),
            gross_margin=_opt(gm_row[date_col] if gm_row is not None else None),
            cash_flow=_opt(cf_row[date_col] if cf_row is not None else None),
        ).to_dict())

    return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "symbol": symbol})


def get_dividend(symbol: str) -> DataResult:
    try:
        with _no_proxy():
            df = ak.stock_fhps_detail_em(symbol=symbol)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_fhps_detail_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_fhps_detail_em", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_fhps_detail_em", f"无数据: {symbol}", "data")

    rows = [DividendRecord(
        symbol=symbol,
        ex_date=str(r.get("除权除息日", "")).replace("-", ""),
        per_share=float(r.get("每股分红", 0)),
        record_date=str(r.get("股权登记日", "")).replace("-", ""),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "symbol": symbol})


def _recent_quarters(n: int = 5) -> list[str]:
    """动态生成最近 n 个季度报告期（含未来当季，向后找最新预告）。"""
    import datetime
    today = datetime.date.today()
    # 季度末月份：3, 6, 9, 12
    quarter_ends = [(3, 31), (6, 30), (9, 30), (12, 31)]
    quarters = []
    year = today.year
    while len(quarters) < n:
        for month, day in reversed(quarter_ends):
            d = datetime.date(year, month, day)
            if d <= today + datetime.timedelta(days=45):  # 允许当季预告提前出现
                quarters.append(d.strftime("%Y%m%d"))
            if len(quarters) >= n:
                break
        year -= 1
    return quarters


def get_earnings_forecast(symbol: str) -> DataResult:
    # stock_yjyg_em 按报告期查全市场，再按 symbol 过滤
    quarters = _recent_quarters(5)
    for quarter in quarters:
        try:
            with _no_proxy():
                df = ak.stock_yjyg_em(date=quarter)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_yjyg_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_yjyg_em", str(e), "data") from e

        if df is None or df.empty:
            continue

        filtered = df[df["股票代码"] == symbol]
        if not filtered.empty:
            rows = [EarningsForecast(
                symbol=symbol,
                period=quarter,
                forecast_type=str(r.get("预告类型", "")),
                net_profit_min=_opt(r.get("预计净利润-下限")),
                net_profit_max=_opt(r.get("预计净利润-上限")),
                change_low=_opt(r.get("预计净利润变动幅度-下限") or r.get("业绩变动幅度")),
                change_high=_opt(r.get("预计净利润变动幅度-上限") or r.get("业绩变动幅度")),
                summary=str(r.get("业绩变动原因", "")),
            ).to_dict() for _, r in filtered.iterrows()]
            return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "symbol": symbol})

    raise DataFetchError("akshare", "stock_yjyg_em", f"近期无业绩预告: {symbol}", "data")
