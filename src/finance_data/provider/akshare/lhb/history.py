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
    def get_lhb_stock_stat_history(self, period: str = "近一月") -> DataResult:
        if period not in _VALID_PERIODS:
            raise DataFetchError("akshare", "stock_lhb_stock_statistic_em",
                                 f"period 必须是 {_VALID_PERIODS} 之一，got: {period!r}", "data")
        try:
            with _no_proxy():
                df = ak.stock_lhb_stock_statistic_em(symbol=period)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_lhb_stock_statistic_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_lhb_stock_statistic_em", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_lhb_stock_statistic_em",
                                 f"无数据: {period}", "data")

        rows = [LhbStockStat(
            symbol=str(r.get("代码", "")),
            name=str(r.get("名称", "")),
            last_date=_date(r.get("最近上榜日", "")),
            times=_int(r.get("上榜次数")),
            lhb_net_buy=_flt(r.get("龙虎榜净买额")),
            lhb_buy=_flt(r.get("龙虎榜买入额")),
            lhb_sell=_flt(r.get("龙虎榜卖出额")),
            lhb_amount=_flt(r.get("龙虎榜总成交额")),
            inst_buy_times=_int(r.get("买方机构次数")),
            inst_sell_times=_int(r.get("卖方机构次数")),
            inst_net_buy=_flt(r.get("机构买入净额")),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "period": period})


class AkshareLhbActiveTraders:
    def get_lhb_active_traders_history(self, start_date: str, end_date: str) -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_lhb_hyyyb_em(start_date=start_date, end_date=end_date)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_lhb_hyyyb_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_lhb_hyyyb_em", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_lhb_hyyyb_em",
                                 f"无数据: {start_date}~{end_date}", "data")

        rows = [LhbActiveTrader(
            branch_name=str(r.get("营业部名称", "")),
            date=_date(r.get("上榜日", "")),
            buy_count=_int(r.get("买入个股数")),
            sell_count=_int(r.get("卖出个股数")),
            buy_amount=_flt(r.get("买入总金额")),
            sell_amount=_flt(r.get("卖出总金额")),
            net_amount=_flt(r.get("总买卖净额")),
            stocks=_str(r.get("买入股票", "")),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "start_date": start_date, "end_date": end_date})


class AkshareLhbTraderStat:
    def get_lhb_trader_stat_history(self, period: str = "近一月") -> DataResult:
        if period not in _VALID_PERIODS:
            raise DataFetchError("akshare", "stock_lhb_traderstatistic_em",
                                 f"period 必须是 {_VALID_PERIODS} 之一，got: {period!r}", "data")
        try:
            with _no_proxy():
                df = ak.stock_lhb_traderstatistic_em(symbol=period)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_lhb_traderstatistic_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_lhb_traderstatistic_em", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_lhb_traderstatistic_em",
                                 f"无数据: {period}", "data")

        rows = [LhbTraderStat(
            branch_name=str(r.get("营业部名称", "")),
            lhb_amount=_flt(r.get("龙虎榜成交金额")),
            times=_int(r.get("上榜次数")),
            buy_amount=_flt(r.get("买入额")),
            buy_times=_int(r.get("买入次数")),
            sell_amount=_flt(r.get("卖出额")),
            sell_times=_int(r.get("卖出次数")),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "period": period})


class AkshareLhbStockDetail:
    def get_lhb_stock_detail_history(self, symbol: str, date: str, flag: str = "买入") -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_lhb_stock_detail_em(symbol=symbol, date=date, flag=flag)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_lhb_stock_detail_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_lhb_stock_detail_em", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_lhb_stock_detail_em",
                                 f"无数据: {symbol} {date} {flag}", "data")

        amount_col = "买入金额" if flag == "买入" else "卖出金额"

        rows = [LhbStockDetail(
            symbol=symbol,
            date=date,
            flag=flag,
            branch_name=_str(r.get("交易营业部名称", "")),
            trade_amount=_flt(r.get(amount_col)),
            buy_rate=_flt(r.get("买入金额-占总成交比例")),
            sell_rate=_flt(r.get("卖出金额-占总成交比例")),
            net_amount=_flt(r.get("净额")),
            seat_type=_str(r.get("类型", "")),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "symbol": symbol, "date": date, "flag": flag})
