"""K线历史数据 - akshare 实现（腾讯源优先）"""
import contextlib
import datetime
import logging
import requests
import akshare as ak

from finance_data.interface.kline.history import KlineBar
from finance_data.interface.types import DataResult, DataFetchError

logger = logging.getLogger(__name__)

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)
_PERIODS_DAILY = {"daily", "weekly", "monthly"}
_PERIODS_MIN = {"1min", "5min", "15min", "30min", "60min"}
_MIN_MAP = {"1min": "1", "5min": "5", "15min": "15", "30min": "30", "60min": "60"}


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


def _symbol_to_tx(symbol: str) -> str:
    """纯数字 symbol 转腾讯格式: 6开头 -> sh, 其余 -> sz"""
    from finance_data.provider.symbol import to_tencent
    return to_tencent(symbol)


def _prev_days(date_str: str, days: int = 5) -> str:
    """将 yyyymmdd 日期往前推 N 天，返回 yyyymmdd"""
    dt = datetime.datetime.strptime(date_str[:8], "%Y%m%d")
    return (dt - datetime.timedelta(days=days)).strftime("%Y%m%d")


def _calc_volume(amount: float, open_: float, high: float, low: float, close: float) -> float:
    """从成交额估算成交量: volume = amount * 1000 / 均价（腾讯源 amount 单位为千元）"""
    avg = (open_ + high + low + close) / 4
    if avg <= 0:
        return 0.0
    return round(amount * 1000 / avg)


def _build_bars_from_tx(df, symbol: str, period: str, adj: str, start: str) -> list:
    """从腾讯源 DataFrame 构建 KlineBar 列表，计算 volume 和 pct_chg。
    多取的前几天仅用于计算首条 pct_chg，最终按 start 截断。"""
    all_bars = []
    prev_close = 0.0
    for _, row in df.iterrows():
        open_ = float(row.get("open", 0))
        high = float(row.get("high", 0))
        low = float(row.get("low", 0))
        close = float(row.get("close", 0))
        amount = float(row.get("amount", 0))
        volume = _calc_volume(amount, open_, high, low, close)
        pct_chg = round((close - prev_close) / prev_close * 100, 2) if prev_close > 0 else 0.0
        prev_close = close
        all_bars.append((
            _parse_date(row.get("date", "")),
            KlineBar(
                symbol=symbol, date=_parse_date(row.get("date", "")),
                period=period,
                open=open_, high=high, low=low, close=close,
                volume=volume, amount=amount * 1000,  # 千元→元
                pct_chg=pct_chg, adj=adj,
            ).to_dict(),
        ))
    # 截断: 只保留 >= start 的数据
    return [bar for date, bar in all_bars if date >= start]


class AkshareKlineHistory:
    def get_kline_history(self, symbol: str, period: str, start: str, end: str,
                          adj: str = "qfq") -> DataResult:
        adj_ak = {"qfq": "qfq", "hfq": "hfq", "none": ""}.get(adj, adj)

        if period in _PERIODS_DAILY:
            return self._get_daily(symbol, period, start, end, adj, adj_ak)
        elif period in _PERIODS_MIN:
            return self._get_minute(symbol, period, start, end, adj, adj_ak)
        else:
            raise DataFetchError("akshare", "get_kline_history",
                                 f"不支持的 period: {period}", "data")

    def _get_daily(self, symbol: str, period: str, start: str, end: str,
                   adj: str, adj_ak: str) -> DataResult:
        # 腾讯源（仅 daily）
        if period == "daily":
            try:
                fetch_start = _prev_days(start, days=5)
                with _no_proxy():
                    df = ak.stock_zh_a_hist_tx(
                        symbol=_symbol_to_tx(symbol),
                        start_date=fetch_start, end_date=end, adjust=adj_ak,
                    )
                if df is not None and not df.empty:
                    bars = _build_bars_from_tx(df, symbol, period, adj, start)
                    if bars:
                        return DataResult(data=bars, source="akshare",
                                          meta={"rows": len(bars), "symbol": symbol,
                                                "period": period, "upstream": "tencent"})
            except DataFetchError:
                raise
            except _NETWORK_ERRORS as e:
                raise DataFetchError("akshare", "get_kline_history", str(e), "network") from e
            except Exception as tx_err:
                logger.info("腾讯源失败: %s", tx_err)

        # weekly/monthly 无腾讯源替代，直接报错
        raise DataFetchError("akshare", "get_kline_history",
                             f"无可用数据源: {symbol} {period} {start}-{end}", "data")

    def _get_minute(self, symbol: str, period: str, start: str, end: str,
                    adj: str, adj_ak: str) -> DataResult:
        # 分钟线仍使用 eastmoney（无替代），失败后由 service 层 fallback 到 tushare
        try:
            with _no_proxy():
                df = ak.stock_zh_a_hist_min_em(
                    symbol=symbol, period=_MIN_MAP[period],
                    start_date=start, end_date=end, adjust=adj_ak,
                )
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "get_kline_history", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "get_kline_history", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "get_kline_history",
                                 f"无数据: {symbol} {period} {start}-{end}", "data")

        bars = []
        for _, row in df.iterrows():
            bars.append(KlineBar(
                symbol=symbol, date=_parse_date(row.get("时间", "")),
                period=period,
                open=float(row.get("开盘", 0)), high=float(row.get("最高", 0)),
                low=float(row.get("最低", 0)), close=float(row.get("收盘", 0)),
                volume=float(row.get("成交量", 0)), amount=float(row.get("成交额", 0)),
                pct_chg=float(row.get("涨跌幅", 0)), adj=adj,
            ).to_dict())

        return DataResult(data=bars, source="akshare",
                          meta={"rows": len(bars), "symbol": symbol,
                                "period": period, "upstream": "eastmoney"})
