"""龙虎榜/游资 - akshare 实现"""
import contextlib
import requests
import akshare as ak

from finance_data.interface.lhb.history import (
    LhbEntry, LhbStockStat, LhbActiveTrader, LhbTraderStat, LhbStockDetail,
)
from finance_data.interface.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)
_VALID_PERIODS = {"近一月", "近三月", "近六月", "近一年"}


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


class AkshareLhbDetail:
    def get_lhb_detail_history(self, start_date: str, end_date: str) -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_lhb_detail_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_lhb_detail_em", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_lhb_detail_em",
                                 f"无数据: {start_date}~{end_date}", "data")

        rows = [LhbEntry(
            symbol=str(r.get("代码", "")),
            name=str(r.get("名称", "")),
            date=_date(r.get("上榜日", "")),
            close=_flt(r.get("收盘价")),
            pct_change=_flt(r.get("涨跌幅")),
            lhb_net_buy=_flt(r.get("龙虎榜净买额")),
            lhb_buy=_flt(r.get("龙虎榜买入额")),
            lhb_sell=_flt(r.get("龙虎榜卖出额")),
            lhb_amount=_flt(r.get("龙虎榜成交额")),
            market_amount=_flt(r.get("市场总成交额")),
            net_rate=_flt(r.get("净买额占总成交比")),
            amount_rate=_flt(r.get("成交额占总成交比")),
            turnover_rate=_flt(r.get("换手率")),
            float_value=_flt(r.get("流通市值")),
            reason=str(r.get("上榜原因", "")),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "start_date": start_date, "end_date": end_date})


class AkshareLhbStockStat:
    """个股上榜统计 - 新浪源（stock_lhb_ggtj_sina，固定返回近5日）"""

    def get_lhb_stock_stat_history(self, period: str = "近一月") -> DataResult:
        # 新浪源无 period 参数，固定返回近 5 日统计
        try:
            with _no_proxy():
                df = ak.stock_lhb_ggtj_sina()
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_lhb_ggtj_sina", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_lhb_ggtj_sina", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_lhb_ggtj_sina", "无数据", "data")

        rows = [LhbStockStat(
            symbol=str(r.get("股票代码", "")),
            name=str(r.get("股票名称", "")),
            last_date="",
            times=_int(r.get("上榜次数")),
            lhb_net_buy=_flt(r.get("净额")),
            lhb_buy=_flt(r.get("累积购买额")),
            lhb_sell=_flt(r.get("累积卖出额")),
            lhb_amount=_flt(r.get("累积购买额")) + _flt(r.get("累积卖出额")),
            inst_buy_times=_int(r.get("买入席位数")),
            inst_sell_times=_int(r.get("卖出席位数")),
            inst_net_buy=0.0,
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "period": period, "upstream": "sina"})


class AkshareLhbActiveTraders:
    """活跃游资营业部 - 新浪源（stock_lhb_yytj_sina，固定返回近期）"""

    def get_lhb_active_traders_history(self, start_date: str, end_date: str) -> DataResult:
        # 新浪源无日期参数，固定返回近期统计
        try:
            with _no_proxy():
                df = ak.stock_lhb_yytj_sina()
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_lhb_yytj_sina", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_lhb_yytj_sina", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_lhb_yytj_sina",
                                 f"无数据", "data")

        rows = [LhbActiveTrader(
            branch_name=str(r.get("营业部名称", "")),
            date="",
            buy_count=_int(r.get("上榜次数")),
            sell_count=0,
            buy_amount=_flt(r.get("累积购买额")),
            sell_amount=_flt(r.get("累积卖出额")),
            net_amount=_flt(r.get("累积购买额")) - _flt(r.get("累积卖出额")),
            stocks=_str(r.get("买入前三股票", "")),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "upstream": "sina"})


class AkshareLhbTraderStat:
    """营业部统计排行 - 新浪源（stock_lhb_yytj_sina，固定返回近期）"""

    def get_lhb_trader_stat_history(self, period: str = "近一月") -> DataResult:
        # 新浪源无 period 参数，固定返回近期统计
        try:
            with _no_proxy():
                df = ak.stock_lhb_yytj_sina()
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_lhb_yytj_sina", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_lhb_yytj_sina", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_lhb_yytj_sina",
                                 f"无数据", "data")

        rows = [LhbTraderStat(
            branch_name=str(r.get("营业部名称", "")),
            lhb_amount=_flt(r.get("累积购买额")) + _flt(r.get("累积卖出额")),
            times=_int(r.get("上榜次数")),
            buy_amount=_flt(r.get("累积购买额")),
            buy_times=_int(r.get("买入席位数")),
            sell_amount=_flt(r.get("累积卖出额")),
            sell_times=_int(r.get("卖出席位数")),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "period": period, "upstream": "sina"})


class AkshareLhbStockDetail:
    """个股龙虎榜席位明细 - 新浪源（stock_lhb_detail_daily_sina，按日期查全部上榜股）"""

    def get_lhb_stock_detail_history(self, symbol: str, date: str, flag: str = "买入") -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_lhb_detail_daily_sina(date=date)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_lhb_detail_daily_sina", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_lhb_detail_daily_sina", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_lhb_detail_daily_sina",
                                 f"无数据: {date}", "data")

        # 新浪源返回当日全部上榜股，若指定 symbol 则过滤
        if symbol:
            code = symbol.replace(".", "").lstrip("0") if len(symbol) <= 6 else symbol
            df = df[df["股票代码"].astype(str).str.contains(symbol)]
            if df.empty:
                # 不过滤，返回全部（新浪不支持按个股筛选）
                with _no_proxy():
                    df = ak.stock_lhb_detail_daily_sina(date=date)

        rows = [LhbStockDetail(
            symbol=str(r.get("股票代码", "")),
            date=date,
            flag="全部",
            branch_name="",
            trade_amount=_flt(r.get("成交额")),
            buy_rate=0.0,
            sell_rate=0.0,
            net_amount=0.0,
            seat_type=_str(r.get("指标", "")),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "date": date, "upstream": "sina"})
