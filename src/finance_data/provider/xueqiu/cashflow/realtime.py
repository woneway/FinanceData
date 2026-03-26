"""个股资金流向 - 雪球实现"""
import datetime
import logging

import requests

from finance_data.interface.cashflow.realtime import FundFlow
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.xueqiu.client import (
    _to_xueqiu_symbol,
    get_session,
    refresh_session,
)

logger = logging.getLogger(__name__)

_ASSORT_URL = "https://stock.xueqiu.com/v5/stock/capital/assort.json"
_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


class XueqiuStockCapitalFlow:
    """雪球个股资金流向 provider（无需登录 cookie）"""

    def get_stock_capital_flow_realtime(self, symbol: str) -> DataResult:
        xq_symbol = _to_xueqiu_symbol(symbol)
        session = get_session()

        data = self._request(session, xq_symbol)
        if data is None:
            session = refresh_session()
            data = self._request(session, xq_symbol)

        if data is None:
            raise DataFetchError(
                "xueqiu", "capital_assort", f"无法获取资金流向: {symbol}", "data"
            )

        flow = self._parse(symbol, data)
        return DataResult(
            data=[flow.to_dict()],
            source="xueqiu",
            meta={"rows": 1, "symbol": symbol},
        )

    def _request(self, session: requests.Session, xq_symbol: str) -> dict | None:
        try:
            resp = session.get(
                _ASSORT_URL,
                params={"symbol": xq_symbol},
                timeout=10,
            )
            resp.raise_for_status()
            body = resp.json()
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            kind = "auth" if status in (401, 403) else "network"
            raise DataFetchError("xueqiu", "capital_assort", str(e), kind) from e
        except _NETWORK_ERRORS as e:
            raise DataFetchError("xueqiu", "capital_assort", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("xueqiu", "capital_assort", str(e), "data") from e

        data = body.get("data")
        if not data or data.get("buy_total") is None:
            return None
        return data

    def _parse(self, symbol: str, d: dict) -> FundFlow:
        buy_total = float(d.get("buy_total", 0) or 0)
        sell_total = float(d.get("sell_total", 0) or 0)
        buy_large = float(d.get("buy_large", 0) or 0)
        sell_large = float(d.get("sell_large", 0) or 0)
        buy_xlarge = d.get("buy_xlarge")
        sell_xlarge = d.get("sell_xlarge")

        net_inflow = buy_total - sell_total
        total_amount = buy_total + sell_total
        net_inflow_pct = (net_inflow / total_amount * 100) if total_amount > 0 else 0.0

        # 超大单可能为 None
        if buy_xlarge is not None and sell_xlarge is not None:
            super_net = float(buy_xlarge) - float(sell_xlarge)
            super_pct = (super_net / total_amount * 100) if total_amount > 0 else 0.0
        else:
            super_net = 0.0
            super_pct = 0.0

        # 主力 = 大单 + 超大单（与东方财富定义一致）
        main_net = (buy_large - sell_large) + super_net
        main_pct = (main_net / total_amount * 100) if total_amount > 0 else 0.0

        # timestamp → date
        ts_ms = d.get("timestamp")
        if ts_ms:
            dt = datetime.datetime.fromtimestamp(
                float(ts_ms) / 1000, tz=datetime.timezone.utc
            )
            date_str = dt.astimezone(
                datetime.timezone(datetime.timedelta(hours=8))
            ).strftime("%Y%m%d")
        else:
            date_str = datetime.date.today().strftime("%Y%m%d")

        return FundFlow(
            symbol=symbol,
            date=date_str,
            net_inflow=round(net_inflow, 2),
            net_inflow_pct=round(net_inflow_pct, 4),
            main_net_inflow=round(main_net, 2),
            main_net_inflow_pct=round(main_pct, 4),
            super_large_net_inflow=round(super_net, 2),
            super_large_net_inflow_pct=round(super_pct, 4),
        )
