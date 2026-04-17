"""腾讯实时行情 API client

接口：http://qt.gtimg.cn/q=sz000001,sh600519
返回：GBK 编码文本，字段以 ~ 分隔
特点：无需 token、无 IP 限流、延迟 ~65ms
"""
import logging
from typing import Optional

import requests

from finance_data.interface.types import DataFetchError
from finance_data.provider.symbol import to_tencent

logger = logging.getLogger(__name__)

_BASE_URL = "http://qt.gtimg.cn/q="
_TIMEOUT = 10

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError, requests.RequestException)

# 腾讯 API 字段索引映射（基于 ~ 分隔的位置）
# 完整字段参考：https://blog.csdn.net/xxxx 等逆向工程文档
_FIELD_INDEX = {
    "market": 0,         # 市场代码
    "name": 1,           # 股票名称
    "code": 2,           # 股票代码
    "current": 3,        # 当前价
    "prev_close": 4,     # 昨收价
    "open": 5,           # 开盘价
    "volume": 6,         # 成交量（手）
    "buy_volume": 7,     # 外盘（手）
    "sell_volume": 8,    # 内盘（手）
    "bid1_price": 9,     # 买一价
    "bid1_volume": 10,   # 买一量
    "bid2_price": 11,
    "bid2_volume": 12,
    "bid3_price": 13,
    "bid3_volume": 14,
    "bid4_price": 15,
    "bid4_volume": 16,
    "bid5_price": 17,
    "bid5_volume": 18,
    "ask1_price": 19,
    "ask1_volume": 20,
    "ask2_price": 21,
    "ask2_volume": 22,
    "ask3_price": 23,
    "ask3_volume": 24,
    "ask4_price": 25,
    "ask4_volume": 26,
    "ask5_price": 27,
    "ask5_volume": 28,
    # 29: 最近逐笔（空）
    "datetime": 30,      # 时间 YYYYMMDDHHmmss
    "change": 31,        # 涨跌额
    "pct_change": 32,    # 涨跌幅 %
    "high": 33,          # 最高价
    "low": 34,           # 最低价
    "current_volume_amount": 35,  # 当前价/成交量/成交额
    "volume_hand": 36,   # 成交量（手）
    "amount_wan": 37,    # 成交额（万元）
    "turnover_rate": 38, # 换手率 %
    "pe": 39,            # 市盈率
    # 40: 空
    "high_52w": 41,      # 52周最高
    "low_52w": 42,       # 52周最低
    "volume_ratio": 43,  # 量比
    "market_cap": 44,    # 总市值（亿元）
    "circ_market_cap": 45,  # 流通市值（亿元）
    "pb": 46,            # 市净率
    "limit_up": 47,      # 涨停价
    "limit_down": 48,    # 跌停价
    "amplitude": 49,     # 振幅 %
    "circ_shares": 50,   # 流通股本
    # 51-54: 涨跌停相关
    # 55-56: 空
    "total_shares": 57,  # 总股本
    # 58-79: 各周期涨跌幅和其他指标
}


def _safe_float(val: str, default: float = 0.0) -> float:
    """安全转浮点，空字符串和无效值返回 default"""
    if not val or val.strip() == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _parse_line(line: str) -> Optional[dict]:
    """解析单只股票的响应行为 dict"""
    # 格式: v_sz000001="字段1~字段2~...~字段N";
    try:
        eq_pos = line.index("=")
        key = line[:eq_pos].strip()  # v_sz000001
        val = line[eq_pos + 1:].strip().strip('";')
    except (ValueError, IndexError):
        return None

    if not val:
        return None

    fields = val.split("~")
    if len(fields) < 50:
        return None

    # 提取 symbol 标识（v_sz000001 → sz000001）
    tc_symbol = key.replace("v_", "")

    return {
        "tc_symbol": tc_symbol,
        "name": fields[_FIELD_INDEX["name"]],
        "code": fields[_FIELD_INDEX["code"]],
        "current": _safe_float(fields[_FIELD_INDEX["current"]]),
        "prev_close": _safe_float(fields[_FIELD_INDEX["prev_close"]]),
        "open": _safe_float(fields[_FIELD_INDEX["open"]]),
        "high": _safe_float(fields[_FIELD_INDEX["high"]]),
        "low": _safe_float(fields[_FIELD_INDEX["low"]]),
        "volume": _safe_float(fields[_FIELD_INDEX["volume_hand"]]) * 100,  # 手→股
        "amount": _safe_float(fields[_FIELD_INDEX["amount_wan"]]) * 10000,  # 万元→元
        "change": _safe_float(fields[_FIELD_INDEX["change"]]),
        "pct_chg": _safe_float(fields[_FIELD_INDEX["pct_change"]]),
        "turnover_rate": _safe_float(fields[_FIELD_INDEX["turnover_rate"]]),
        "pe": _safe_float(fields[_FIELD_INDEX["pe"]]),
        "pb": _safe_float(fields[_FIELD_INDEX["pb"]]),
        "market_cap": _safe_float(fields[_FIELD_INDEX["market_cap"]]) * 1e8,  # 亿→元
        "circ_market_cap": _safe_float(fields[_FIELD_INDEX["circ_market_cap"]]) * 1e8,  # 亿→元
        "volume_ratio": _safe_float(fields[_FIELD_INDEX["volume_ratio"]]),
        "limit_up": _safe_float(fields[_FIELD_INDEX["limit_up"]]),
        "limit_down": _safe_float(fields[_FIELD_INDEX["limit_down"]]),
        "amplitude": _safe_float(fields[_FIELD_INDEX["amplitude"]]),
        "datetime": fields[_FIELD_INDEX["datetime"]] if len(fields) > _FIELD_INDEX["datetime"] else "",
        # 买卖五档
        "bid1_price": _safe_float(fields[_FIELD_INDEX["bid1_price"]]),
        "bid1_volume": _safe_float(fields[_FIELD_INDEX["bid1_volume"]]),
        "ask1_price": _safe_float(fields[_FIELD_INDEX["ask1_price"]]),
        "ask1_volume": _safe_float(fields[_FIELD_INDEX["ask1_volume"]]),
    }


def fetch_quotes(symbols: list[str]) -> list[dict]:
    """批量获取腾讯实时行情

    Args:
        symbols: 任意格式的股票代码列表，如 ["000001", "600519"]

    Returns:
        解析后的行情 dict 列表，单位已转换（volume=股, amount=元, market_cap=元）

    Raises:
        DataFetchError: 网络错误或无数据
    """
    if not symbols:
        return []

    tc_symbols = [to_tencent(s) for s in symbols]
    url = _BASE_URL + ",".join(tc_symbols)

    try:
        resp = requests.get(url, timeout=_TIMEOUT)
        resp.encoding = "gbk"
        text = resp.text
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tencent", "qt.gtimg.cn", str(e), "network") from e

    results = []
    for line in text.strip().split(";"):
        line = line.strip()
        if not line:
            continue
        parsed = _parse_line(line)
        if parsed and parsed["current"] > 0:
            results.append(parsed)

    return results


def fetch_quote(symbol: str) -> dict:
    """获取单只股票的腾讯实时行情

    Raises:
        DataFetchError: 网络错误或无数据
    """
    results = fetch_quotes([symbol])
    if not results:
        raise DataFetchError("tencent", "qt.gtimg.cn", f"无数据: {symbol}", "data")
    return results[0]
