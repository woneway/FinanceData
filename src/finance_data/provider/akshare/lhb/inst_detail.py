"""龙虎榜机构明细 - akshare 实现（东财源，需绕过代理）"""
import akshare as ak

from finance_data.provider.akshare._proxy import ensure_eastmoney_no_proxy

ensure_eastmoney_no_proxy()

from finance_data.interface.lhb.history import LhbInstDetail
from finance_data.interface.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _flt(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if v != v else v
    except (TypeError, ValueError):
        return default


def _int(val, default: int = 0) -> int:
    try:
        v = float(val)
        if v != v or v == float("inf") or v == float("-inf"):
            return default
        return int(v)
    except (TypeError, ValueError):
        return default


def _date(val) -> str:
    if val is None:
        return ""
    s = str(val).replace("-", "")[:8]
    return s if s.isdigit() else ""


def _str(val) -> str:
    if val is None:
        return ""
    try:
        if float(val) != float(val):
            return ""
    except (TypeError, ValueError):
        pass
    return str(val)


class AkshareLhbInstDetail:
    """龙虎榜机构买卖明细 - 东财源（stock_lhb_jgmmtj_em）"""

    def get_lhb_inst_detail_history(self, start_date: str, end_date: str) -> DataResult:
        try:
            df = ak.stock_lhb_jgmmtj_em(start_date=start_date, end_date=end_date)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_lhb_jgmmtj_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_lhb_jgmmtj_em", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_lhb_jgmmtj_em",
                                 f"无数据: {start_date}~{end_date}", "data")

        rows = [LhbInstDetail(
            symbol=str(r.get("代码", "")),
            name=str(r.get("名称", "")),
            close=_flt(r.get("收盘价")),
            pct_chg=_flt(r.get("涨跌幅")),
            inst_buy_count=_int(r.get("买方机构数")),
            inst_sell_count=_int(r.get("卖方机构数")),
            inst_buy_amount=_flt(r.get("机构买入总额")),
            inst_sell_amount=_flt(r.get("机构卖出总额")),
            inst_net_buy=_flt(r.get("机构买入净额")),
            market_amount=_flt(r.get("市场总成交额")),
            inst_net_rate=_flt(r.get("机构净买额占总成交额比")),
            turnover_rate=_flt(r.get("换手率")),
            float_value=_flt(r.get("流通市值")),
            reason=_str(r.get("上榜原因")),
            date=_date(r.get("上榜日期")),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "start_date": start_date, "end_date": end_date})
