"""热股排行 - akshare 实现（东财源，需绕过代理）"""
import akshare as ak

from finance_data.provider.akshare._proxy import ensure_eastmoney_no_proxy

ensure_eastmoney_no_proxy()

from finance_data.interface.hot_rank.realtime import HotRankEntry
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


class AkshareHotRank:
    """热股排行 - 东财源（stock_hot_rank_em）"""

    def get_hot_rank_realtime(self) -> DataResult:
        try:
            df = ak.stock_hot_rank_em()
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_hot_rank_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_hot_rank_em", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_hot_rank_em", "无数据", "data")

        rows = [HotRankEntry(
            rank=_int(r.get("当前排名")),
            symbol=str(r.get("代码", "")).replace("SZ", "").replace("SH", ""),
            name=str(r.get("股票名称", "")),
            latest_price=_flt(r.get("最新价")),
            change_amount=_flt(r.get("涨跌额")),
            pct_chg=_flt(r.get("涨跌幅")),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows)})
