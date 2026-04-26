"""MCP 接入层 — aggregator only。

物理结构：
- `_app.py`     — FastMCP 单例 `mcp` + helpers (`_to_json`, `_invoke_tool_json`)
- `tools/<domain>.py` × 14 — 各 domain 的 `@mcp.tool` 装饰函数
- `server.py`   — 本文件，仅做两件事：
  1. 按确定顺序 import 14 个 tools 子模块以触发 `@mcp.tool` 注册
  2. re-export 全部 service 实例与 mcp，保持外部 import 入口与测试 mock 路径兼容

外部 import 入口：
- `from finance_data.mcp.server import mcp` — 共享 FastMCP 单例
- `patch("finance_data.mcp.server.<service>.<method>")` — 测试 mock 路径

本文件 14 个 tools import 顺序与 `tool_specs/registry/__init__.py` 中的
`_DOMAIN_ORDER` 保持一致；`tests/mcp/test_tools_layout.py` 守护两者顺序。
"""
# === FastMCP 单例 + helpers re-export（mcp 是关键对外入口）===
from finance_data.mcp._app import mcp, _to_json, _invoke_tool_json  # noqa: F401

# === 按确定顺序 import 14 个 tools 子模块以触发 @mcp.tool 注册 ===
# 同时 re-export 全部 48 个 tool 函数以兼容
# `from finance_data.mcp.server import tool_get_xxx` 形式的测试 import。
from finance_data.mcp.tools.stock import (  # noqa: F401
    tool_get_stock_info_snapshot,
    tool_get_stock_basic_list_snapshot,
)
from finance_data.mcp.tools.kline import (  # noqa: F401
    tool_get_kline_daily_history,
    tool_get_kline_weekly_history,
    tool_get_kline_monthly_history,
    tool_get_kline_minute_history,
)
from finance_data.mcp.tools.quote import tool_get_stock_quote_realtime  # noqa: F401
from finance_data.mcp.tools.index import (  # noqa: F401
    tool_get_index_quote_realtime,
    tool_get_index_kline_history,
)
from finance_data.mcp.tools.board import (  # noqa: F401
    tool_get_board_index_history,
    tool_get_board_member_history,
    tool_get_board_kline_history,
)
from finance_data.mcp.tools.fundamental import (  # noqa: F401
    tool_get_chip_distribution_history,
    tool_get_financial_summary_history,
    tool_get_dividend_history,
)
from finance_data.mcp.tools.cashflow import tool_get_capital_flow_realtime  # noqa: F401
from finance_data.mcp.tools.market import (  # noqa: F401
    tool_get_trade_calendar_history,
    tool_get_market_stats_realtime,
    tool_get_suspend_daily,
    tool_get_hot_rank_realtime,
    tool_get_ths_hot_history,
    tool_get_auction_history,
    tool_get_auction_close_history,
    tool_get_daily_market_history,
    tool_get_daily_basic_market_history,
    tool_get_stk_limit_daily,
)
from finance_data.mcp.tools.lhb import (  # noqa: F401
    tool_get_lhb_detail_history,
    tool_get_lhb_stock_stat_history,
    tool_get_lhb_active_traders_history,
    tool_get_lhb_trader_stat_history,
    tool_get_lhb_stock_detail_daily,
    tool_get_lhb_inst_detail_history,
    tool_get_hm_list_snapshot,
    tool_get_hm_detail_history,
)
from finance_data.mcp.tools.pool import (  # noqa: F401
    tool_get_zt_pool_daily,
    tool_get_strong_stocks_daily,
    tool_get_previous_zt_daily,
    tool_get_zbgc_pool_daily,
    tool_get_limit_list_history,
    tool_get_kpl_list_history,
    tool_get_limit_step_history,
)
from finance_data.mcp.tools.north_flow import (  # noqa: F401
    tool_get_north_hold_history,
    tool_get_north_capital_snapshot,
)
from finance_data.mcp.tools.margin import (  # noqa: F401
    tool_get_margin_history,
    tool_get_margin_detail_history,
)
from finance_data.mcp.tools.technical import tool_get_stock_factor_pro_history  # noqa: F401
from finance_data.mcp.tools.fund_flow import (  # noqa: F401
    tool_get_dc_board_moneyflow_history,
    tool_get_dc_market_moneyflow_history,
)

# === re-export 全部 service 实例（保持测试 mock 路径兼容）===
# 形如 `patch("finance_data.mcp.server.stock_history.get_stock_info_history")` 的测试
# 依赖以下 service 实例挂在本模块名字空间下。任何 service 名变更必须同步此处 + tests。
from finance_data.service.stock import stock_history, stock_basic_list  # noqa: F401
from finance_data.service.kline import (  # noqa: F401
    daily_kline_history,
    weekly_kline_history,
    monthly_kline_history,
    minute_kline_history,
)
from finance_data.service.realtime import realtime_quote  # noqa: F401
from finance_data.service.index import index_quote, index_history  # noqa: F401
from finance_data.service.board import board_index, board_member, board_daily  # noqa: F401
from finance_data.service.chip import chip_history  # noqa: F401
from finance_data.service.fundamental import financial_summary, dividend  # noqa: F401
from finance_data.service.cashflow import stock_capital_flow  # noqa: F401
from finance_data.service.calendar import trade_calendar  # noqa: F401
from finance_data.service.market import market_realtime, auction, auction_close  # noqa: F401
from finance_data.service.lhb import (  # noqa: F401
    lhb_detail,
    lhb_stock_stat,
    lhb_active_traders,
    lhb_trader_stat,
    lhb_stock_detail,
    lhb_inst_detail,
    hm_list,
    hm_detail,
)
from finance_data.service.pool import (  # noqa: F401
    zt_pool,
    strong_stocks,
    previous_zt,
    zbgc_pool,
    limit_list,
    kpl_list,
    limit_step,
)
from finance_data.service.north_flow import north_flow, north_stock_hold  # noqa: F401
from finance_data.service.margin import margin, margin_detail  # noqa: F401
from finance_data.service.suspend import suspend  # noqa: F401
from finance_data.service.hot_rank import hot_rank, ths_hot  # noqa: F401
from finance_data.service.daily_market import daily_market  # noqa: F401
from finance_data.service.daily_basic import daily_basic_market  # noqa: F401
from finance_data.service.stk_limit import stk_limit  # noqa: F401
from finance_data.service.technical import stock_factor  # noqa: F401
from finance_data.service.fund_flow import board_moneyflow, market_moneyflow  # noqa: F401
