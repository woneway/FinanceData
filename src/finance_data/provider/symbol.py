"""
统一的 symbol 格式转换模块。

所有 provider 的 symbol 转换逻辑收敛于此，避免散落在各处导致不一致。

输入格式规范（统一）：
  - 纯 6 位数字: 000001, 600519, 399001
  - .SH/.SZ 后缀: 000001.SH, 399001.SZ
  - sh/sz/SH/SZ 前缀: sh000001, SZ399001

MCP 层和 Service 层原样透传，规范化在各 Provider 内部完成。
"""

# ============================================================
# 标准化层：任意格式 → (纯 6 位数字, 交易所)
# ============================================================


def normalize(symbol: str) -> tuple[str, str]:
    """
    将任意格式的 symbol 规范化为 (code, exchange)。

    支持: 000001, 000001.SH, sh000001, SZ000001 等
    返回: ("000001", "SH") 或 ("000001", "SZ")

    交易所推断规则：
      - .SH/.SZ 后缀 → 显式指定（优先级最高）
      - sh/SZ/SH/SZ 前缀 → 显式指定（sh/sz → SZ，SH → SH）
      - 无后缀/前缀时（现有行为兼容）：
        - 6xxxx → SH（上交所股票）
        - 000xxx → SZ（深交所股票/指数；000001.SH 为上交所指数）
        - 399xxx → SZ（深交所指数）
        - 其他 → SZ
    """
    s = symbol.strip()
    upper = s.upper()

    # 优先检测显式后缀 .SH/.SZ（不区分大小写）
    if upper.endswith(".SH"):
        exchange = "SH"
        code_part = s[:-3].strip()  # 保留原始大小写以便处理前缀
    elif upper.endswith(".SZ"):
        exchange = "SZ"
        code_part = s[:-3].strip()
    else:
        code_part = s
        exchange = None

    # 去掉 sh/sz/SH/SZ 前缀（按原始大小写匹配）
    prefix_exchange: str | None = None
    for pfx in ("SH", "SZ", "sh", "sz"):
        if code_part.startswith(pfx):
            code_part = code_part[len(pfx):]
            # SH → SH（上交所），sh/sz/SZ → SZ（深交所）
            prefix_exchange = "SH" if pfx == "SH" else "SZ"
            break

    # 去掉所有非数字字符，提取纯数字
    digits = "".join(c for c in code_part if c.isdigit())
    code = digits.zfill(6)

    # 交易所推断：优先用显式后缀/前缀；无则根据代码首位（zfill 前判断）
    if exchange is None:
        if prefix_exchange is not None:
            exchange = prefix_exchange
        else:
            # 无前缀：仅 6xxxx → SH（上交所），其余 → SZ（深交所）
            exchange = "SH" if digits.startswith("6") else "SZ"

    return code, exchange


def to_tushare(symbol: str) -> str:
    """
    任意格式 → tushare 格式（000001.SZ / 000001.SH）。

    雪球/腾讯格式 → tushare: SZ000001 → 000001.SZ
    """
    code, exchange = normalize(symbol)
    return f"{code}.{exchange}"


def to_xueqiu(symbol: str) -> str:
    """
    任意格式 → 雪球格式（SZ000001 / SH600519）。

    tushare 格式 → 雪球: 000001.SH → SH000001
    """
    code, exchange = normalize(symbol)
    return f"{exchange}{code}"


def to_tencent(symbol: str) -> str:
    """
    任意格式 → 腾讯格式（sz000001 / sh600519）。

    用于 akshare 的 stock_zh_index_daily_tx 等腾讯源接口。
    """
    code, exchange = normalize(symbol)
    return f"{exchange.lower()}{code}"


def to_eastmoney(symbol: str) -> str:
    """
    任意格式 → eastmoney 格式（纯 6 位数字）。

    用于 akshare 的 stock_zh_a_hist_min_em 等东财源接口。
    """
    code, _ = normalize(symbol)
    return code


def to_sina(symbol: str) -> str:
    """
    任意格式 → 新浪格式（sz000001 / sh000001）。

    用于 akshare 的 stock_zh_index_spot_sina 等新浪源接口。
    """
    code, exchange = normalize(symbol)
    return f"{exchange.lower()}{code}"


def is_index(symbol: str) -> bool:
    """判断是否为指数代码（000xxx 或 399xxx）。"""
    code, _ = normalize(symbol)
    return code.startswith("000") or code.startswith("399")


# ============================================================
# 指数雪球特殊映射：xueqiu 指数 API 使用硬编码映射表
# ============================================================

_XUEQIU_INDEX_MAP: dict[str, str] = {
    "000001": "SH000001",   # 上证指数
    "399001": "SZ399001",   # 深证成指
    "399006": "SZ399006",   # 创业板指
    "000300": "SH000300",   # 沪深300
    "000016": "SH000016",   # 上证50
    "000905": "SH000905",   # 中证500
    "000852": "SH000852",   # 中证1000
}


def to_xueqiu_index(symbol: str) -> str:
    """
    任意格式 → 雪球指数格式。

    优先使用硬编码映射表（针对常见宽基指数），兜底使用首位规则。
    雪球指数 API 对部分指数有特殊代码，非简单前缀拼接。
    """
    code, exchange = normalize(symbol)
    if code in _XUEQIU_INDEX_MAP:
        return _XUEQIU_INDEX_MAP[code]
    # fallback: 首位规则
    return f"{exchange}{code}"
