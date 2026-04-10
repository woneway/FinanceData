"""K线历史数据 - akshare 实现（仅腾讯源日线）"""
import contextlib
import datetime
import logging
import requests
import akshare as ak

from finance_data.interface.kline.history import KlineBar
from finance_data.interface.types import DataResult, DataFetchError

logger = logging.getLogger(__name__)

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


def _symbol_to_tx(symbol: str) -> str:
    """纯数字 symbol 转腾讯格式: 6开头 -> sh, 其余 -> sz"""
    from finance_data.provider.symbol import to_tencent
    return to_tencent(symbol)


def _prev_days(date_str: str, days: int = 5) -> str:
    """将 yyyymmdd 日期往前推 N 天，返回 yyyymmdd"""
    dt = datetime.datetime.strptime(date_str[:8], "%Y%m%d")
    return (dt - datetime.timedelta(days=days)).strftime("%Y%m%d")


def _build_bars_from_tx(df, symbol: str, period: str, adj: str, start: str) -> list:
    """从腾讯源 DataFrame 构建 KlineBar 列表。
    腾讯源 "amount" 列实为成交量（手），需 *100 转股；成交额从 volume*均价 估算。
    多取的前几天仅用于计算首条 pct_chg，最终按 start 截断。"""
    all_bars = []
    prev_close = 0.0
    for _, row in df.iterrows():
        open_ = float(row.get("open", 0))
        high = float(row.get("high", 0))
        low = float(row.get("low", 0))
        close = float(row.get("close", 0))
        raw = float(row.get("amount", 0))
        volume = round(raw * 100)  # 腾讯源 "amount" 实为成交量（手→股）
        avg = (open_ + high + low + close) / 4
        amount = round(volume * avg, 2) if avg > 0 else 0.0  # 估算成交额（元）
        pct_chg = round((close - prev_close) / prev_close * 100, 2) if prev_close > 0 else 0.0
        prev_close = close
        all_bars.append((
            _parse_date(row.get("date", "")),
            KlineBar(
                symbol=symbol, date=_parse_date(row.get("date", "")),
                period=period,
                open=open_, high=high, low=low, close=close,
                volume=volume, amount=amount,
                pct_chg=pct_chg, adj=adj,
            ).to_dict(),
        ))
    # 截断: 只保留 >= start 的数据
    return [bar for date, bar in all_bars if date >= start]


def _get_daily_tx(symbol: str, start: str, end: str, adj: str,
                  adj_ak: str, func_name: str) -> DataResult:
    """腾讯源日线。"""
    try:
        fetch_start = _prev_days(start, days=5)
        with _no_proxy():
            df = ak.stock_zh_a_hist_tx(
                symbol=_symbol_to_tx(symbol),
                start_date=fetch_start, end_date=end, adjust=adj_ak,
            )
        if df is not None and not df.empty:
            bars = _build_bars_from_tx(df, symbol, "daily", adj, start)
            if bars:
                return DataResult(data=bars, source="akshare",
                                  meta={"rows": len(bars), "symbol": symbol,
                                        "period": "daily", "upstream": "tencent"})
    except DataFetchError:
        raise
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", func_name, str(e), "network") from e
    except Exception as tx_err:
        logger.info("腾讯源日线失败: %s", tx_err)

    raise DataFetchError("akshare", func_name,
                         f"无可用数据源: {symbol} daily {start}-{end}", "data")

class AkshareKlineHistory:
    def get_kline_history(self, symbol: str, period: str, start: str, end: str,
                          adj: str = "qfq") -> DataResult:
        adj_ak = {"qfq": "qfq", "hfq": "hfq", "none": ""}.get(adj, adj)

        if period == "daily":
            return _get_daily_tx(symbol, start, end, adj, adj_ak, "get_kline_history")
        else:
            raise DataFetchError("akshare", "get_kline_history",
                                 f"不支持的 period: {period}", "data")

    def get_daily_kline_history(self, symbol: str, start: str, end: str,
                                adj: str = "qfq") -> DataResult:
        adj_ak = {"qfq": "qfq", "hfq": "hfq", "none": ""}.get(adj, adj)
        return _get_daily_tx(symbol, start, end, adj, adj_ak,
                             "get_daily_kline_history")
