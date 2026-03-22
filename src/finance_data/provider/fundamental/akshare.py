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

    rows = [FinancialSummary(
        symbol=symbol,
        period=str(r.get("报告期", "")).replace("-", ""),
        revenue=_opt(r.get("营业总收入")),
        net_profit=_opt(r.get("净利润")),
        roe=_opt(r.get("净资产收益率")),
        gross_margin=_opt(r.get("毛利率")),
        cash_flow=_opt(r.get("经营现金流量净额")),
    ).to_dict() for _, r in df.iterrows()]

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


def get_earnings_forecast(symbol: str) -> DataResult:
    try:
        with _no_proxy():
            df = ak.stock_yjyg_em(symbol=symbol)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_yjyg_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_yjyg_em", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_yjyg_em", f"无数据: {symbol}", "data")

    rows = [EarningsForecast(
        symbol=symbol,
        period=str(r.get("报告期", "")).replace("-", ""),
        forecast_type=str(r.get("业绩变动类型", "")),
        change_low=_opt(r.get("业绩变动幅度-低")),
        change_high=_opt(r.get("业绩变动幅度-高")),
        summary=str(r.get("业绩变动原因", "")),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "symbol": symbol})
