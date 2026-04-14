"""
集成测试脚本：对所有保留的 provider 接口进行真实 API 调用测试。
（东财源已全部禁用，相关测试已移除）
运行：python tests/integration_test.py

网络说明：
  akshare 内部使用 _no_proxy() 将 requests.Session.trust_env 设为 False，
  绕过系统代理环境变量。在 Clash fake-ip 模式下，所有域名解析到假 IP 导致直连失败。
  解决方案：在 requests.Session.__init__ 预注入 explicit proxies dict，
  explicit proxies 优先级高于 trust_env=False，使流量经由本机 Clash 代理正确路由。

  如需跳过代理注入：NO_PROXY_INJECT=1 python tests/integration_test.py
  如需自定义代理地址：INTEGRATION_PROXY=http://127.0.0.1:7890 python tests/integration_test.py
"""
import os
import sys
import time
import datetime
import traceback

# ─── 代理注入（必须在所有 provider import 之前）───
# 脉动VPN / Clash mixed-port 7892；经代理后域名由 Clash 解析，绕过 fake-ip
_CLASH_PROXY = os.environ.get("INTEGRATION_PROXY", "http://127.0.0.1:7892")
_PROXY_ENABLED = os.environ.get("NO_PROXY_INJECT", "").strip().lower() not in ("1", "true", "yes")

if _PROXY_ENABLED:
    import requests as _req
    _orig_init = _req.Session.__init__

    def _proxied_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        self.proxies = {"http": _CLASH_PROXY, "https": _CLASH_PROXY}

    _req.Session.__init__ = _proxied_init
    print(f"[proxy] 注入 requests.Session.proxies → {_CLASH_PROXY}")
else:
    print("[proxy] 代理注入已跳过（NO_PROXY_INJECT=1）")

# 确保项目 src 可导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from finance_data.interface.types import DataFetchError  # noqa: E402

# ───────────────────────────── helpers ─────────────────────────────

GREEN = "\033[32m"
RED   = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

results: list[dict] = []

def run(tool: str, provider: str, fn, *args, **kwargs):
    """执行单个接口测试，记录结果。"""
    start = time.time()
    try:
        result = fn(*args, **kwargs)
        elapsed = time.time() - start
        rows = len(result.data) if hasattr(result, "data") else 0
        sample = result.data[0] if rows > 0 else {}
        print(f"  {GREEN}PASS{RESET} {rows} 行  {elapsed:.2f}s")
        results.append({
            "tool": tool, "provider": provider,
            "status": "PASS", "rows": rows, "time": elapsed,
            "error": "", "sample_keys": list(sample.keys()) if sample else [],
        })
    except DataFetchError as e:
        elapsed = time.time() - start
        msg = f"[{e.kind}] {e.reason}"
        print(f"  {RED}FAIL{RESET} DataFetchError: {msg}  {elapsed:.2f}s")
        results.append({
            "tool": tool, "provider": provider,
            "status": "FAIL", "rows": 0, "time": elapsed,
            "error": msg, "sample_keys": [],
        })
    except Exception as e:
        elapsed = time.time() - start
        msg = traceback.format_exc(limit=3).strip().splitlines()[-1]
        print(f"  {RED}FAIL{RESET} {type(e).__name__}: {msg}  {elapsed:.2f}s")
        results.append({
            "tool": tool, "provider": provider,
            "status": "FAIL", "rows": 0, "time": elapsed,
            "error": f"{type(e).__name__}: {msg}", "sample_keys": [],
        })


def section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {YELLOW}{title}{RESET}")
    print(f"{'─'*60}")


# ───────────────────────── 近期可用日期 ─────────────────────────────

# 最近的交易日（周末往前推）
today = datetime.date.today()
# 上周五
offset = (today.weekday() - 4) % 7
last_friday = today - datetime.timedelta(days=offset if offset else 7)
trade_date = last_friday.strftime("%Y%m%d")
trade_date_prev = (last_friday - datetime.timedelta(days=7)).strftime("%Y%m%d")
print(f"使用交易日: {trade_date}  (上上周: {trade_date_prev})")

# ───────────────────────────── 测试 ─────────────────────────────────

section("1. stock — 个股基本信息")

# akshare stock_info 已禁用（东财源）
print("  [tushare] get_stock_info (000001)...")
from finance_data.provider.tushare.stock.history import TushareStockHistory
run("tool_get_stock_info", "tushare", TushareStockHistory().get_stock_info_history, "000001")


section("2. kline — K线历史")

print("  [akshare] get_kline daily (000001 20250101-20250320)...")
from finance_data.provider.akshare.kline.history import AkshareKlineHistory
run("tool_get_kline", "akshare",
    AkshareKlineHistory().get_kline_history,
    "000001", "daily", "20250101", "20250320", "qfq")

print("  [tushare] get_kline daily (000001 20250101-20250320)...")
from finance_data.provider.tushare.kline.history import TushareKlineHistory
run("tool_get_kline", "tushare",
    TushareKlineHistory().get_kline_history,
    "000001", "daily", "20250101", "20250320", "qfq")


section("3. realtime — 实时行情")

# akshare realtime 已禁用（东财源不可用，新浪源太慢）
print("  [tushare] get_realtime_quote (000001)...")
from finance_data.provider.tushare.realtime.realtime import TushareRealtimeQuote
run("tool_get_stock_quote_realtime", "tushare",
    TushareRealtimeQuote().get_realtime_quote, "000001")


section("4. index — 大盘指数实时行情")

print("  [akshare] get_index_quote (000001.SH)...")
from finance_data.provider.akshare.index.realtime import AkshareIndexQuote
run("tool_get_index_quote", "akshare",
    AkshareIndexQuote().get_index_quote_realtime, "000001.SH")

print("  [tushare] get_index_quote (000001.SH)...")
from finance_data.provider.tushare.index.realtime import TushareIndexQuote
run("tool_get_index_quote", "tushare",
    TushareIndexQuote().get_index_quote_realtime, "000001.SH")


section("5. index — 大盘指数历史K线")

print("  [akshare] get_index_history (000001.SH 20250101-20250320)...")
from finance_data.provider.akshare.index.history import AkshareIndexHistory
run("tool_get_index_kline_history", "akshare",
    AkshareIndexHistory().get_index_history, "000001.SH", "20250101", "20250320")

print("  [tushare] get_index_history (000001.SH 20250101-20250320)...")
from finance_data.provider.tushare.index.history import TushareIndexHistory
run("tool_get_index_kline_history", "tushare",
    TushareIndexHistory().get_index_history, "000001.SH", "20250101", "20250320")


section("6. board — 东财板块索引")

print("  [tushare] get_board_index (行业板块)...")
from finance_data.provider.tushare.board.index import TushareBoardIndex
run("tool_get_board_index_history", "tushare",
    TushareBoardIndex().get_board_index, "行业板块")


section("7. chip — 个股筹码分布")

# akshare chip 已禁用（依赖东财 stock_cyq_em）
print("  [tushare] get_chip_distribution (000001)...")
from finance_data.provider.tushare.chip.history import TushareChipHistory
run("tool_get_chip_distribution", "tushare",
    TushareChipHistory().get_chip_distribution_history, "000001")


section("8. fundamental — 财务摘要")

print("  [akshare] get_financial_summary (000001)...")
from finance_data.provider.akshare.fundamental.history import AkshareFinancialSummary
run("tool_get_financial_summary", "akshare",
    AkshareFinancialSummary().get_financial_summary_history, "000001")

print("  [tushare] get_financial_summary (000001)...")
from finance_data.provider.tushare.fundamental.history import TushareFinancialSummary
run("tool_get_financial_summary", "tushare",
    TushareFinancialSummary().get_financial_summary_history, "000001")


section("9. fundamental — 历史分红")

print("  [akshare] get_dividend (000001)...")
from finance_data.provider.akshare.fundamental.history import AkshareDividend
run("tool_get_dividend", "akshare",
    AkshareDividend().get_dividend_history, "000001")

print("  [tushare] get_dividend (000001)...")
from finance_data.provider.tushare.fundamental.history import TushareDividend
run("tool_get_dividend", "tushare",
    TushareDividend().get_dividend_history, "000001")


# section 10 (业绩预告) 已禁用（依赖东财 stock_yjyg_em）
# section 11 (个股资金流向 akshare) 已禁用（依赖东财 stock_individual_fund_flow）


section("12. calendar — 交易日历")

print("  [tushare] get_trade_calendar (20250101-20250331)...")
from finance_data.provider.tushare.calendar.history import TushareTradeCalendar
run("tool_get_trade_calendar", "tushare",
    TushareTradeCalendar().get_trade_calendar_history, "20250101", "20250331")


section("13. market — 市场涨跌统计")

print("  [akshare] get_market_stats_realtime...")
from finance_data.provider.akshare.market.realtime import AkshareMarketRealtime
run("tool_get_market_stats_realtime", "akshare",
    AkshareMarketRealtime().get_market_stats_realtime)


section("14. lhb — 龙虎榜详情")

lhb_start = trade_date_prev
lhb_end = trade_date
# akshare lhb 已禁用（依赖东财 stock_lhb_detail_em）
print(f"  [tushare] get_lhb_detail ({trade_date})...")
from finance_data.provider.tushare.lhb.history import TushareLhbDetail
run("tool_get_lhb_detail_history", "tushare",
    TushareLhbDetail().get_lhb_detail_history, trade_date, trade_date)

# sections 15-18 (lhb_stock_stat, active_traders, trader_stat, stock_detail) 已禁用（东财源）
# sections 19-22 (zt_pool, strong_stocks, previous_zt, zbgc_pool) 已禁用（东财源）
# section 23 (north_flow 日频) 已禁用（东财源）

section("15. north_flow — 北向持股明细")

print("  [tushare] get_north_stock_hold (600519.SH 20240815)...")
from finance_data.provider.tushare.north_flow.history import TushareNorthStockHold
run("tool_get_north_hold_history", "tushare",
    TushareNorthStockHold().get_north_stock_hold_history,
    symbol="600519.SH", trade_date="20240815")


section("16. margin — 融资融券汇总")

print(f"  [akshare] get_margin (trade_date={trade_date})...")
from finance_data.provider.akshare.margin.history import AkshareMargin
run("tool_get_margin_history", "akshare",
    AkshareMargin().get_margin_history, trade_date=trade_date)

print(f"  [tushare] get_margin (trade_date={trade_date})...")
from finance_data.provider.tushare.margin.history import TushareMargin
run("tool_get_margin_history", "tushare",
    TushareMargin().get_margin_history, trade_date=trade_date)


section("17. margin — 融资融券个股明细")

print(f"  [akshare] get_margin_detail (trade_date={trade_date})...")
from finance_data.provider.akshare.margin.history import AkshareMarginDetail
run("tool_get_margin_detail_history", "akshare",
    AkshareMarginDetail().get_margin_detail_history, trade_date=trade_date)

print(f"  [tushare] get_margin_detail (trade_date={trade_date})...")
from finance_data.provider.tushare.margin.history import TushareMarginDetail
run("tool_get_margin_detail_history", "tushare",
    TushareMarginDetail().get_margin_detail_history, trade_date=trade_date)


# section 27 (sector_fund_flow) 已禁用（依赖东财 stock_sector_fund_flow_rank）


# ───────────────────────── 汇总 & 报告 ─────────────────────────────

print(f"\n{'═'*60}")
passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")
skipped = sum(1 for r in results if r["status"] == "SKIP")
total = len(results)
print(f"  汇总: {GREEN}{passed} PASS{RESET} / {RED}{failed} FAIL{RESET} / {YELLOW}{skipped} SKIP{RESET}  共 {total} 项")
print(f"{'═'*60}")

# 生成 TEST_REPORT.md
report_path = os.path.join(os.path.dirname(__file__), "..", "TEST_REPORT.md")

now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

lines = [
    "# Provider 集成测试报告",
    "",
    f"> 生成时间：{now_str}",
    f"> 测试交易日：{trade_date}",
    "",
    f"## 汇总：{passed} PASS / {failed} FAIL / {skipped} SKIP（共 {total} 项）",
    "",
    "| # | Tool | Provider | 状态 | 行数 | 耗时(s) | 备注 |",
    "|---|------|----------|------|------|---------|------|",
]

tool_seq = [
    "tool_get_stock_info",
    "tool_get_kline",
    "tool_get_stock_quote_realtime",
    "tool_get_index_quote",
    "tool_get_index_kline_history",
    "tool_get_board_index_history",
    "tool_get_chip_distribution",
    "tool_get_financial_summary",
    "tool_get_dividend",
    "tool_get_trade_calendar",
    "tool_get_market_stats_realtime",
    "tool_get_lhb_detail_history",
    "tool_get_north_hold_history",
    "tool_get_margin_history",
    "tool_get_margin_detail_history",
]

STATUS_EMOJI = {"PASS": "✅", "FAIL": "❌", "SKIP": "⚠️"}

idx = 1
for tool in tool_seq:
    tool_results = [r for r in results if r["tool"] == tool]
    for r in tool_results:
        emoji = STATUS_EMOJI.get(r["status"], "")
        note = r["error"] if r["status"] != "PASS" else ""
        lines.append(
            f"| {idx} | `{r['tool']}` | {r['provider']} | {emoji} {r['status']} "
            f"| {r['rows']} | {r['time']:.2f} | {note} |"
        )
        idx += 1

lines += [
    "",
    "## 失败详情",
    "",
]

fail_results = [r for r in results if r["status"] == "FAIL"]
if fail_results:
    for r in fail_results:
        lines.append(f"### `{r['tool']}` ({r['provider']})")
        lines.append(f"- 错误：`{r['error']}`")
        lines.append("")
else:
    lines.append("_无失败项_ 🎉")
    lines.append("")

lines += [
    "## 跳过详情",
    "",
]

skip_results = [r for r in results if r["status"] == "SKIP"]
if skip_results:
    for r in skip_results:
        lines.append(f"### `{r['tool']}` ({r['provider']})")
        lines.append(f"- 原因：`{r['error']}`")
        lines.append("")
else:
    lines.append("_无跳过项_")
    lines.append("")

with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\n报告已生成：{report_path}")
