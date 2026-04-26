"""MCP tools — quote domain。

由 mcp/server.py 按确定顺序 import 触发 @mcp.tool 注册。
本模块不应被外部直接 import。
"""
from finance_data.interface.types import DataFetchError  # noqa: F401
from finance_data.mcp._app import mcp, _invoke_tool_json

from finance_data.service.realtime import realtime_quote


@mcp.tool()
async def tool_get_stock_quote_realtime(symbol: str) -> str:
    """
    获取股票实时行情（价格/涨跌/量能/PE/PB/市值/换手率/量比/涨跌停价）。

    数据源: xueqiu(实时价格) + tencent(量比/流通市值/涨跌停价)
    实时性: 盘中实时（T+0）
    历史查询: 不支持
    缓存: 有（20 分钟）

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        JSON 列表，每条包含：symbol(代码)、name(名称)、price(当前价元)、
        pct_chg(涨跌幅%)、volume(成交量股)、amount(成交额元)、
        market_cap(总市值元)、pe(市盈率)、pb(市净率)、
        turnover_rate(换手率%)、timestamp(ISO 8601)、
        circ_market_cap(流通市值元)、volume_ratio(量比)、
        limit_up(涨停价元)、limit_down(跌停价元)、prev_close(昨收价元)

    Note:
        腾讯补充字段为 best-effort，失败时仅返回雪球核心字段。
    """
    return _invoke_tool_json("tool_get_stock_quote_realtime", {"symbol": symbol})
