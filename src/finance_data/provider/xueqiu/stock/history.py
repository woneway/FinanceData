"""个股基本信息 - 雪球实现"""
import datetime
import logging

import requests

from finance_data.interface.stock.history import StockInfo
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.xueqiu.client import (
    _to_xueqiu_symbol,
    get_session,
    refresh_session,
)
from finance_data.provider.symbol import to_xueqiu

logger = logging.getLogger(__name__)

_COMPANY_URL = "https://stock.xueqiu.com/v5/stock/f10/cn/company.json"
_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _str(val) -> str:
    if val is None:
        return ""
    return str(val)


_CN_TZ = datetime.timezone(datetime.timedelta(hours=8))


def _ms_to_date(val) -> str:
    """Convert millisecond timestamp to YYYYMMDD string (UTC+8)."""
    if val is None:
        return ""
    try:
        ts = float(val) / 1000
        dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        return dt.astimezone(_CN_TZ).strftime("%Y%m%d")
    except (TypeError, ValueError, OSError):
        return ""


class XueqiuStockHistory:
    """雪球个股基本信息 provider（无需登录 cookie）"""

    def get_stock_info_history(self, symbol: str) -> DataResult:
        xq_symbol = _to_xueqiu_symbol(symbol)
        session = get_session()

        data = self._request(session, xq_symbol)
        if data is None:
            session = refresh_session()
            data = self._request(session, xq_symbol)

        if data is None:
            raise DataFetchError(
                "xueqiu", "company", f"无法获取个股信息: {symbol}", "data"
            )

        info = self._parse(symbol, data)
        return DataResult(
            data=[info.to_dict()],
            source="xueqiu",
            meta={"rows": 1, "symbol": symbol},
        )

    def _request(self, session: requests.Session, xq_symbol: str) -> dict | None:
        try:
            resp = session.get(
                _COMPANY_URL,
                params={"symbol": xq_symbol},
                timeout=10,
            )
            resp.raise_for_status()
            body = resp.json()
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            kind = "auth" if status in (401, 403) else "network"
            raise DataFetchError("xueqiu", "company", str(e), kind) from e
        except _NETWORK_ERRORS as e:
            raise DataFetchError("xueqiu", "company", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("xueqiu", "company", str(e), "data") from e

        company = body.get("data", {}).get("company")
        if not company:
            return None
        return company

    def _parse(self, symbol: str, d: dict) -> StockInfo:
        industry_info = d.get("affiliate_industry") or {}
        industry = _str(industry_info.get("ind_name", ""))

        return StockInfo(
            symbol=symbol,
            name=_str(d.get("org_short_name_cn", "")),
            industry=industry,
            list_date=_ms_to_date(d.get("listed_date")),
            area=_str(d.get("provincial_name", "")),
            exchange="SSE" if to_xueqiu(symbol).startswith("SH") else "SZSE",
            full_name=_str(d.get("org_name_cn", "")),
            established_date=_ms_to_date(d.get("established_date")),
            main_business=_str(d.get("main_operation_business", "")),
            introduction=_str(d.get("org_cn_introduction", "")),
            chairman=_str(d.get("chairman", "")),
            legal_representative=_str(d.get("legal_representative", "")),
            general_manager=_str(d.get("general_manager", "")),
            secretary=_str(d.get("secretary", "")),
            reg_capital=float(d["reg_asset"]) if d.get("reg_asset") else None,
            staff_num=int(d["staff_num"]) if d.get("staff_num") else None,
            website=_str(d.get("org_website", "")),
            email=_str(d.get("email", "")),
            reg_address=_str(d.get("reg_address_cn", "")),
        )
