"""MCP tools — technical domain。

由 mcp/server.py 按确定顺序 import 触发 @mcp.tool 注册。
本模块不应被外部直接 import。
"""
from finance_data.interface.types import DataFetchError  # noqa: F401
from finance_data.mcp._app import mcp, _invoke_tool_json

from finance_data.service.technical import stock_factor


@mcp.tool()
async def tool_get_stock_factor_pro_history(
    ts_code: str = "",
    trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
) -> str:
    """
    获取股票技术面因子专业版（MA/MACD/KDJ/RSI/BOLL/CCI + 估值/量价）。

    数据源: tushare(stk_factor_pro)
    实时性: 收盘后更新（T+1_16:00）
    历史查询: 支持（2005年至今）

    Args:
        ts_code: 股票代码（tushare格式），如 "000001.SZ"
        trade_date: 交易日期 YYYYMMDD（与 start_date/end_date 二选一）
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD

    Returns:
        JSON 列表，每条包含：trade_date、symbol、close(元)、volume(股)、amount(元)、
        ma5/10/20/30/60/90/250(不复权)、macd_dif/macd_dea/macd、kdj_k/kdj_d/kdj_j、
        rsi_6/12/24、boll_upper/mid/lower、cci、pe_ttm、pb、turnover_rate(%)、
        pct_chg(涨跌幅%)、total_mv(总市值元)、circ_mv(流通市值元)

    Note:
        需 5000 积分权限，单次最多 10000 条。
    """
    return _invoke_tool_json(
        "tool_get_stock_factor_pro_history",
        {"ts_code": ts_code, "trade_date": trade_date,
         "start_date": start_date, "end_date": end_date},
    )
