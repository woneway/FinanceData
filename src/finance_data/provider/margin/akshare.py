"""融资融券 - akshare"""
import contextlib
import requests
import akshare as ak

from finance_data.provider.margin.models import MarginSummary, MarginDetail
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


def _parse_date(val) -> str:
    s = str(val).strip().replace("-", "").replace(" ", "")[:8]
    return s if s.isdigit() else ""


def _safe_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _yi_to_yuan(v) -> float:
    """亿元转元。"""
    return _safe_float(v) * 1e8


def get_margin(
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
    exchange_id: str = "",
) -> DataResult:
    """
    获取融资融券汇总数据（按交易所）。

    数据源:
    - stock_margin_sse(start_date, end_date): 上交所，单位是 元
    - stock_margin_szse(date): 深交所，单位是 亿元，需转换为元
    注意：akshare 只支持单日查询，忽略 start_date/end_date 日期范围。

    Args:
        trade_date: 交易日期 YYYYMMDD（如 "20250110"），空则取最新
        start_date: 开始日期（akshare 忽略，仅 tushare 支持范围查询）
        end_date: 结束日期（akshare 忽略）
        exchange_id: 交易所过滤（"SSE"/"SZSE"/"BSE"），空则返回全部

    Returns:
        DataResult，data 为 [MarginSummary.to_dict(), ...]
    """
    # akshare 只支持单日，使用 trade_date 或 start_date 作为查询日期
    date = trade_date or start_date
    rows = []

    # 上交所 SSE（参数是 start_date/end_date）
    if not exchange_id or exchange_id == "SSE":
        try:
            with _no_proxy():
                if date:
                    df_sse = ak.stock_margin_sse(start_date=date, end_date=date)
                else:
                    df_sse = ak.stock_margin_sse()
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_margin_sse", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_margin_sse", str(e), "data") from e

        if df_sse is not None and not df_sse.empty:
            for _, row in df_sse.iterrows():
                date_val = _parse_date(row.get("信用交易日期", ""))
                rows.append(MarginSummary(
                    date=date_val,
                    exchange="SSE",
                    rzye=_safe_float(row.get("融资余额")),
                    rzmre=_safe_float(row.get("融资买入额")),
                    rzche=0,  # akshare 无此字段
                    rqye=_safe_float(row.get("融券余量金额")),
                    rqmcl=_safe_float(row.get("融券卖出量")),
                    rzrqye=_safe_float(row.get("融资融券余额")),
                    rqyl=_safe_float(row.get("融券余量")),
                ).to_dict())

    # 深交所 SZSE（参数是 date，单位是亿元）
    if not exchange_id or exchange_id == "SZSE":
        try:
            with _no_proxy():
                if date:
                    df_szse = ak.stock_margin_szse(date=date)
                else:
                    df_szse = ak.stock_margin_szse()
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_margin_szse", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_margin_szse", str(e), "data") from e

        if df_szse is not None and not df_szse.empty:
            for _, row in df_szse.iterrows():
                date_val = _parse_date(row.get("信用交易日期", row.get("日期", date)))
                rows.append(MarginSummary(
                    date=date_val,
                    exchange="SZSE",
                    rzye=_yi_to_yuan(row.get("融资余额")),
                    rzmre=_yi_to_yuan(row.get("融资买入额")),
                    rzche=0,
                    rqye=_yi_to_yuan(row.get("融券余额")),
                    rqmcl=_safe_float(row.get("融券卖出量")),
                    rzrqye=_yi_to_yuan(row.get("融资融券余额")),
                    rqyl=_safe_float(row.get("融券余量")),
                ).to_dict())

    if not rows:
        raise DataFetchError("akshare", "get_margin", f"无数据: date={date}", "data")

    # 按日期倒序
    rows.sort(key=lambda x: x["date"], reverse=True)
    return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "date": date})


def get_margin_detail(
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
    ts_code: str = "",
) -> DataResult:
    """
    获取融资融券个股明细。

    数据源：akshare stock_margin_detail_sse（上交所）
    注意：akshare 只支持单日查询，忽略 start_date/end_date 范围和 ts_code 过滤。

    Args:
        trade_date: 交易日期 YYYYMMDD（如 "20240301"）
        start_date: 开始日期（akshare 忽略）
        end_date: 结束日期（akshare 忽略）
        ts_code: 股票代码（akshare 忽略，无法单只查询）

    Returns:
        DataResult，data 为 [MarginDetail.to_dict(), ...]
    """
    date = trade_date or start_date
    if not date:
        import datetime
        date = datetime.date.today().strftime("%Y%m%d")

    try:
        with _no_proxy():
            df = ak.stock_margin_detail_sse(date=date)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_margin_detail_sse", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_margin_detail_sse", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_margin_detail_sse",
                           f"无数据: date={date}", "data")

    rows = []
    for _, row in df.iterrows():
        code = str(row.get("标的证券代码", "")).strip()
        if not code:
            continue
        rows.append(MarginDetail(
            date=date,
            symbol=code,
            name=str(row.get("标的证券简称", "") or ""),
            rzye=_safe_float(row.get("融资余额")),
            rqye=0,  # akshare SSE 无此字段
            rzmre=_safe_float(row.get("融资买入额")),
            rqyl=0,
            rzche=_safe_float(row.get("融资偿还额")),
            rqchl=0,
            rqmcl=_safe_float(row.get("融券卖出量")),
            rzrqye=0,
        ).to_dict())

    return DataResult(data=rows, source="akshare",
                     meta={"rows": len(rows), "date": date})
