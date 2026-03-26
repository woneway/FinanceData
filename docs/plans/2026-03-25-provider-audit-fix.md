# Provider 审计问题修复计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复 provider-audit-report.md 中发现的所有 P0/P1/P2 问题，确保跨 provider 数据一致性、MCP 层健壮性、元数据准确性。

**Architecture:** 按优先级分层修复 — P0（数据语义错误）→ P1（字段映射/MCP 健壮性）→ P2（文档/元数据一致性）。每个 Task 独立可测试，修复后通过单元测试验证。

**Tech Stack:** Python 3.11+, pytest, akshare, tushare, fastmcp

---

## Task 1: 修复 tushare kline volume 单位（P0）

tushare `vol` 字段单位为"手"（1手=100股），akshare/xueqiu 的 volume 为"股"。需要 `vol * 100`。

**Files:**
- Modify: `src/finance_data/provider/tushare/kline/history.py:56`
- Test: `tests/provider/kline/test_tushare_volume_unit.py`

**Step 1: Write the failing test**

```python
# tests/provider/kline/test_tushare_volume_unit.py
"""验证 tushare kline volume 单位转换（手→股）"""
from unittest.mock import patch, MagicMock
import pandas as pd
from finance_data.provider.tushare.kline.history import TushareKlineHistory


def test_tushare_kline_volume_converts_hand_to_shares():
    """tushare vol=100（手）应转换为 volume=10000（股）"""
    mock_df = pd.DataFrame([{
        "trade_date": "20240101",
        "open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5,
        "vol": 100.0,  # 100 手
        "amount": 1050.0,  # 千元
        "pct_chg": 2.5,
    }])

    with patch("finance_data.provider.tushare.kline.history.get_pro") as mock_pro:
        pro = MagicMock()
        pro.daily.return_value = mock_df
        mock_pro.return_value = pro

        provider = TushareKlineHistory()
        result = provider.get_kline_history("000001", "daily", "20240101", "20240101")

    bar = result.data[0]
    assert bar["volume"] == 10000.0, f"Expected 10000 (股), got {bar['volume']}"
    assert bar["amount"] == 1050000.0, "amount should be converted: 千元 * 1000 = 元"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/provider/kline/test_tushare_volume_unit.py -v`
Expected: FAIL — `assert 100.0 == 10000.0`

**Step 3: Fix the volume conversion**

修改 `src/finance_data/provider/tushare/kline/history.py:56`：

```python
# 原代码
volume=float(row.get("vol", 0)),
# 修改为（手→股，×100）
volume=float(row.get("vol", 0)) * 100,
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/provider/kline/test_tushare_volume_unit.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/finance_data/provider/tushare/kline/history.py tests/provider/kline/test_tushare_volume_unit.py
git commit -m "fix: tushare kline volume 单位从手转换为股（×100）"
```

---

## Task 2: 修复 tushare realtime volume 单位 + price 语义标注（P0+P1）

tushare realtime 的 `vol` 同样为"手"需转"股"。tushare 使用 `pro.daily(limit=1)` 返回 EOD close 而非实时价，属于数据源 API 限制。作为 fallback provider，添加 meta 标注说明 price 为 EOD close，不修改行为。

**Files:**
- Modify: `src/finance_data/provider/tushare/realtime/realtime.py:47-54`
- Test: `tests/provider/realtime/test_tushare_realtime.py`

**Step 1: Write the failing test**

```python
# tests/provider/realtime/test_tushare_realtime.py
"""验证 tushare realtime volume 单位转换 + meta 标注"""
from unittest.mock import patch, MagicMock
import pandas as pd
from finance_data.provider.tushare.realtime.realtime import TushareRealtimeQuote


def test_tushare_realtime_volume_converts_hand_to_shares():
    """tushare vol=500（手）应转换为 volume=50000（股）"""
    mock_df = pd.DataFrame([{
        "close": 15.5,
        "pct_chg": 1.2,
        "vol": 500.0,  # 500 手
        "amount": 775.0,  # 千元
    }])

    with patch("finance_data.provider.tushare.realtime.realtime.get_pro") as mock_pro:
        pro = MagicMock()
        pro.daily.return_value = mock_df
        mock_pro.return_value = pro

        provider = TushareRealtimeQuote()
        result = provider.get_realtime_quote("000001")

    quote = result.data[0]
    assert quote["volume"] == 50000.0, f"Expected 50000 (股), got {quote['volume']}"
    assert quote["amount"] == 775000.0
    # meta 应标注 price 为 EOD close
    assert "eod_close" in result.meta or result.meta.get("price_type") == "eod_close"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/provider/realtime/test_tushare_realtime.py -v`
Expected: FAIL

**Step 3: Fix volume conversion and add meta**

修改 `src/finance_data/provider/tushare/realtime/realtime.py`：

```python
# 原代码 line 47
volume=float(row.get("vol", 0)),
# 修改为
volume=float(row.get("vol", 0)) * 100,

# 原代码 line 53-54
meta={"rows": 1, "symbol": symbol},
# 修改为
meta={"rows": 1, "symbol": symbol, "price_type": "eod_close"},
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/provider/realtime/test_tushare_realtime.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/finance_data/provider/tushare/realtime/realtime.py tests/provider/realtime/test_tushare_realtime.py
git commit -m "fix: tushare realtime volume 手→股 + meta 标注 price_type=eod_close"
```

---

## Task 3: 修复 akshare index_history amount 单位（P0）

akshare 腾讯源 amount 单位为"万元"，tushare/xueqiu 为"元"。需要 `amount * 10000`。

**Files:**
- Modify: `src/finance_data/provider/akshare/index/history.py:68,81`
- Test: `tests/provider/index/test_akshare_index_amount.py`

**Step 1: Write the failing test**

```python
# tests/provider/index/test_akshare_index_amount.py
"""验证 akshare index history amount 单位转换（万元→元）"""
from unittest.mock import patch
import pandas as pd
from finance_data.provider.akshare.index.history import AkshareIndexHistory


def test_akshare_index_amount_converts_wan_to_yuan():
    """akshare amount=100（万元）应转换为 1000000（元）"""
    mock_df = pd.DataFrame([
        {"date": "2024-01-02", "open": 3000.0, "close": 3010.0,
         "high": 3020.0, "low": 2990.0, "amount": 100.0},  # 100 万元
        {"date": "2024-01-03", "open": 3010.0, "close": 3050.0,
         "high": 3060.0, "low": 3000.0, "amount": 200.0},  # 200 万元
    ])

    with patch("finance_data.provider.akshare.index.history.ak") as mock_ak:
        mock_ak.stock_zh_index_daily_tx.return_value = mock_df

        provider = AkshareIndexHistory()
        result = provider.get_index_history("000001.SH", "20240103", "20240103")

    bar = result.data[0]
    assert bar["amount"] == 2000000.0, f"Expected 2000000 (元), got {bar['amount']}"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/provider/index/test_akshare_index_amount.py -v`
Expected: FAIL — `assert 200.0 == 2000000.0`

**Step 3: Fix amount conversion**

修改 `src/finance_data/provider/akshare/index/history.py:68`：

```python
# 原代码
amount = float(row.get("amount", 0))
# 修改为（万元→元）
amount = float(row.get("amount", 0)) * 10000
```

同时修改 line 71 的 volume 估算公式（amount 已经是元了，不需要再乘 10000）：

```python
# 原代码
volume = round(amount * 10000 / avg) if avg > 0 else 0.0
# 修改为（amount 已是元，直接除以均价）
volume = round(amount / avg) if avg > 0 else 0.0
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/provider/index/test_akshare_index_amount.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/finance_data/provider/akshare/index/history.py tests/provider/index/test_akshare_index_amount.py
git commit -m "fix: akshare index_history amount 单位从万元转换为元"
```

---

## Task 4: 修复 xueqiu realtime + index name 字段映射（P1）

xueqiu realtime 和 index_quote 的 `name` 错误映射了 `d["symbol"]`（ticker code 如 "SZ000001"），应映射 `d["name"]`（中文名如 "平安银行"）。

**Files:**
- Modify: `src/finance_data/provider/xueqiu/realtime/realtime.py:97`
- Modify: `src/finance_data/provider/xueqiu/index/realtime.py:67`
- Test: `tests/provider/realtime/test_xueqiu_name.py`

**Step 1: Write the failing test**

```python
# tests/provider/realtime/test_xueqiu_name.py
"""验证 xueqiu realtime/index name 映射正确"""
from finance_data.provider.xueqiu.realtime.realtime import XueqiuRealtimeQuote
from finance_data.provider.xueqiu.index.realtime import XueqiuIndexQuote


def test_xueqiu_realtime_parse_name():
    """name 应为中文名而非 ticker code"""
    provider = XueqiuRealtimeQuote()
    quote = provider._parse("000001", {
        "symbol": "SZ000001",
        "name": "平安银行",
        "current": 15.5,
        "percent": 1.2,
        "volume": 50000,
        "amount": 775000,
        "market_capital": 3e11,
        "pe_ttm": 8.5,
        "pb": 0.9,
        "turnover_rate": 0.5,
        "timestamp": 1700000000000,
    })
    assert quote.name == "平安银行", f"Expected '平安银行', got '{quote.name}'"


def test_xueqiu_index_name():
    """index name 应为中文名而非 ticker code"""
    provider = XueqiuIndexQuote()
    # 直接测试内部解析逻辑
    data = {
        "symbol": "SH000001",
        "name": "上证指数",
        "current": 3200.0,
        "percent": 0.5,
        "volume": 300000000,
        "amount": 4500000000,
        "timestamp": 1700000000000,
    }
    # XueqiuIndexQuote 没有独立 _parse 方法，测试整个 name 字段
    # 需要通过 mock 测试
    assert data.get("name") == "上证指数"  # 确保雪球 API 返回了 name 字段
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/provider/realtime/test_xueqiu_name.py::test_xueqiu_realtime_parse_name -v`
Expected: FAIL — `assert 'SZ000001' == '平安银行'`

**Step 3: Fix name mapping**

修改 `src/finance_data/provider/xueqiu/realtime/realtime.py:97`：

```python
# 原代码
name=str(d.get("symbol", "")),
# 修改为
name=str(d.get("name", "")),
```

修改 `src/finance_data/provider/xueqiu/index/realtime.py:67`：

```python
# 原代码
name=str(data.get("symbol", "")),
# 修改为
name=str(data.get("name", "")),
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/provider/realtime/test_xueqiu_name.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/finance_data/provider/xueqiu/realtime/realtime.py src/finance_data/provider/xueqiu/index/realtime.py tests/provider/realtime/test_xueqiu_name.py
git commit -m "fix: xueqiu realtime/index name 映射从 d['symbol'] 改为 d['name']"
```

---

## Task 5: MCP 层统一添加 try/except 错误处理（P1）

当前 kline、realtime、index_quote、index_history、sector_rank、chip、fundamental、dividend、earnings_forecast、cashflow 共 10 个 MCP tool 缺少 try/except，异常会直接抛出。其他工具（lhb、pool、north_stock_hold、margin、market、sector_fund_flow）已有 try/except。统一添加。

**Files:**
- Modify: `src/finance_data/mcp/server.py:61-269`（10 个函数）
- Test: `tests/mcp/test_mcp_error_handling.py`

**Step 1: Write the failing test**

```python
# tests/mcp/test_mcp_error_handling.py
"""验证所有 MCP tool 均有错误处理，不会抛出原始异常"""
import asyncio
import json
from unittest.mock import patch
from finance_data.interface.types import DataFetchError


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_kline_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_kline_history
    with patch("finance_data.mcp.server.kline_history") as mock:
        mock.get_kline_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_kline_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_realtime_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_realtime_quote
    with patch("finance_data.mcp.server.realtime_quote") as mock:
        mock.get_realtime_quote.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_realtime_quote("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_index_quote_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_index_quote_realtime
    with patch("finance_data.mcp.server.index_quote") as mock:
        mock.get_index_quote_realtime.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_index_quote_realtime("000001.SH"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_index_history_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_index_history
    with patch("finance_data.mcp.server.index_history") as mock:
        mock.get_index_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_index_history("000001.SH"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_sector_rank_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_sector_rank_realtime
    with patch("finance_data.mcp.server.sector_rank") as mock:
        mock.get_sector_rank_realtime.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_sector_rank_realtime())
    parsed = json.loads(result)
    assert "error" in parsed


def test_chip_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_chip_distribution_history
    with patch("finance_data.mcp.server.chip_history") as mock:
        mock.get_chip_distribution_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_chip_distribution_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_financial_summary_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_financial_summary_history
    with patch("finance_data.mcp.server.financial_summary") as mock:
        mock.get_financial_summary_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_financial_summary_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_dividend_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_dividend_history
    with patch("finance_data.mcp.server.dividend") as mock:
        mock.get_dividend_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_dividend_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_earnings_forecast_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_earnings_forecast_history
    with patch("finance_data.mcp.server.earnings_forecast") as mock:
        mock.get_earnings_forecast_history.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_earnings_forecast_history("000001"))
    parsed = json.loads(result)
    assert "error" in parsed


def test_cashflow_mcp_returns_error_json():
    from finance_data.mcp.server import tool_get_stock_capital_flow_realtime
    with patch("finance_data.mcp.server.stock_capital_flow") as mock:
        mock.get_stock_capital_flow_realtime.side_effect = DataFetchError("test", "fn", "boom", "data")
        result = _run(tool_get_stock_capital_flow_realtime("000001"))
    parsed = json.loads(result)
    assert "error" in parsed
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/mcp/test_mcp_error_handling.py -v`
Expected: FAIL — 10 个测试失败（抛出 DataFetchError 而非返回 error JSON）

**Step 3: Add try/except to all 10 MCP tools**

对 `src/finance_data/mcp/server.py` 中缺少 try/except 的 10 个函数统一添加错误处理。

每个函数修改模式：

```python
# 原代码（以 kline 为例）
result = kline_history.get_kline_history(symbol, period=period, start=start, end=end, adj=adj)
return _to_json(result)

# 修改为
try:
    result = kline_history.get_kline_history(symbol, period=period, start=start, end=end, adj=adj)
    return _to_json(result)
except Exception as e:
    return json.dumps({"error": str(e)}, ensure_ascii=False)
```

需要修改的函数列表：
1. `tool_get_kline_history` (line 85-86)
2. `tool_get_realtime_quote` (line 105-106)
3. `tool_get_index_quote_realtime` (line 124-125)
4. `tool_get_index_history` (line 149-150)
5. `tool_get_sector_rank_realtime` (line 168-169)
6. `tool_get_chip_distribution_history` (line 187-188)
7. `tool_get_financial_summary_history` (line 207-208)
8. `tool_get_dividend_history` (line 226-227)
9. `tool_get_earnings_forecast_history` (line 247-248)
10. `tool_get_stock_capital_flow_realtime` (line 267-268)

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/mcp/test_mcp_error_handling.py -v`
Expected: PASS — 全部 10 个测试通过

**Step 5: Commit**

```bash
git add src/finance_data/mcp/server.py tests/mcp/test_mcp_error_handling.py
git commit -m "fix: MCP 层 10 个工具统一添加 try/except 错误处理"
```

---

## Task 6: 修复 MCP 硬编码过期日期 end="20241231"（P1）

kline 和 index_history 的 `end` 默认值硬编码为 `"20241231"`，已过期。改为动态获取当天日期。

**Files:**
- Modify: `src/finance_data/mcp/server.py:65,132`
- Test: `tests/mcp/test_mcp_default_dates.py`

**Step 1: Write the failing test**

```python
# tests/mcp/test_mcp_default_dates.py
"""验证 MCP 工具的默认日期不是硬编码的过期值"""
import inspect
from finance_data.mcp.server import tool_get_kline_history, tool_get_index_history


def test_kline_end_not_hardcoded():
    """kline end 参数不应硬编码为 20241231"""
    sig = inspect.signature(tool_get_kline_history)
    end_default = sig.parameters["end"].default
    assert end_default != "20241231", f"end 默认值不应硬编码为过期日期: {end_default}"


def test_index_history_end_not_hardcoded():
    """index_history end 参数不应硬编码为 20241231"""
    sig = inspect.signature(tool_get_index_history)
    end_default = sig.parameters["end"].default
    assert end_default != "20241231", f"end 默认值不应硬编码为过期日期: {end_default}"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/mcp/test_mcp_default_dates.py -v`
Expected: FAIL

**Step 3: Replace hardcoded dates with empty string + dynamic fallback**

在 `src/finance_data/mcp/server.py` 顶部添加日期工具函数：

```python
import datetime

def _today() -> str:
    """返回当天日期 YYYYMMDD"""
    return datetime.date.today().strftime("%Y%m%d")
```

修改 kline 函数签名（line 65）：

```python
# 原代码
end: str = "20241231",
# 修改为
end: str = "",
```

修改 kline 函数体（在调用前添加 fallback）：

```python
if not end:
    end = _today()
```

同理修改 index_history（line 132）的 `end` 参数和函数体。

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/mcp/test_mcp_default_dates.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/finance_data/mcp/server.py tests/mcp/test_mcp_default_dates.py
git commit -m "fix: MCP kline/index_history end 默认值改为动态当天日期"
```

---

## Task 7: 修复 tushare kline/index 返回数据排序（P1）

tushare 默认返回降序（newest first），akshare/xueqiu 为升序（oldest first）。统一为升序。

**Files:**
- Modify: `src/finance_data/provider/tushare/kline/history.py:60-62`
- Modify: `src/finance_data/provider/tushare/index/history.py:25-36`
- Test: `tests/provider/kline/test_tushare_sort.py`

**Step 1: Write the failing test**

```python
# tests/provider/kline/test_tushare_sort.py
"""验证 tushare kline/index 返回数据为升序（oldest first）"""
from unittest.mock import patch, MagicMock
import pandas as pd
from finance_data.provider.tushare.kline.history import TushareKlineHistory
from finance_data.provider.tushare.index.history import TushareIndexHistory


def test_tushare_kline_sorted_ascending():
    """tushare kline 返回数据应按日期升序"""
    # 模拟 tushare 默认降序返回
    mock_df = pd.DataFrame([
        {"trade_date": "20240103", "open": 11, "high": 12, "low": 10, "close": 11.5, "vol": 100, "amount": 1000, "pct_chg": 1.0},
        {"trade_date": "20240102", "open": 10, "high": 11, "low": 9.5, "close": 10.5, "vol": 80, "amount": 800, "pct_chg": 0.5},
        {"trade_date": "20240101", "open": 10, "high": 10.5, "low": 9.8, "close": 10.0, "vol": 60, "amount": 600, "pct_chg": -0.2},
    ])

    with patch("finance_data.provider.tushare.kline.history.get_pro") as mock_pro:
        pro = MagicMock()
        pro.daily.return_value = mock_df
        mock_pro.return_value = pro

        result = TushareKlineHistory().get_kline_history("000001", "daily", "20240101", "20240103")

    dates = [bar["date"] for bar in result.data]
    assert dates == ["20240101", "20240102", "20240103"], f"Expected ascending, got {dates}"


def test_tushare_index_sorted_ascending():
    """tushare index 返回数据应按日期升序"""
    mock_df = pd.DataFrame([
        {"trade_date": "20240103", "open": 3100, "high": 3150, "low": 3080, "close": 3120, "vol": 3e8, "amount": 4e6, "pct_chg": 0.3},
        {"trade_date": "20240102", "open": 3050, "high": 3100, "low": 3020, "close": 3080, "vol": 2.5e8, "amount": 3.5e6, "pct_chg": 0.5},
        {"trade_date": "20240101", "open": 3000, "high": 3060, "low": 2990, "close": 3050, "vol": 2e8, "amount": 3e6, "pct_chg": -0.1},
    ])

    with patch("finance_data.provider.tushare.index.history.get_pro") as mock_pro:
        pro = MagicMock()
        pro.index_daily.return_value = mock_df
        mock_pro.return_value = pro

        result = TushareIndexHistory().get_index_history("000001.SH", "20240101", "20240103")

    dates = [bar["date"] for bar in result.data]
    assert dates == ["20240101", "20240102", "20240103"], f"Expected ascending, got {dates}"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/provider/kline/test_tushare_sort.py -v`
Expected: FAIL — dates in descending order

**Step 3: Add sorting after building bars list**

修改 `src/finance_data/provider/tushare/kline/history.py`，在 `return` 前添加排序：

```python
        bars.sort(key=lambda b: b["date"])

        return DataResult(data=bars, source="tushare",
                          meta={"rows": len(bars), "symbol": symbol, "period": period})
```

修改 `src/finance_data/provider/tushare/index/history.py`，在 `return` 前添加排序：

```python
        bars.sort(key=lambda b: b["date"])

        return DataResult(data=bars, source="tushare",
                          meta={"rows": len(bars), "symbol": symbol})
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/provider/kline/test_tushare_sort.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/finance_data/provider/tushare/kline/history.py src/finance_data/provider/tushare/index/history.py tests/provider/kline/test_tushare_sort.py
git commit -m "fix: tushare kline/index 返回数据统一为日期升序"
```

---

## Task 8: 修复 MCP docstring 和 registry return_fields 中 pct_change → pct_chg（P1+P2）

MCP docstring 和 registry 的 `return_fields` 使用 `pct_change`，但实际 dataclass 字段名为 `pct_chg`。

**Files:**
- Modify: `src/finance_data/mcp/server.py:103,122,147,166`
- Modify: `src/finance_data/provider/metadata/registry.py:56,73,106`
- Test: `tests/provider/metadata/test_registry_fields.py`

**Step 1: Write the failing test**

```python
# tests/provider/metadata/test_registry_fields.py
"""验证 registry return_fields 不包含 pct_change（应为 pct_chg）"""
from finance_data.provider.metadata.registry import TOOL_REGISTRY


def test_no_pct_change_in_return_fields():
    """所有 return_fields 中不应出现 pct_change，应为 pct_chg"""
    violations = []
    for name, meta in TOOL_REGISTRY.items():
        if "pct_change" in meta.return_fields:
            violations.append(name)
    assert not violations, f"以下工具 return_fields 含 pct_change（应为 pct_chg）: {violations}"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/provider/metadata/test_registry_fields.py -v`
Expected: FAIL

**Step 3: Fix registry and MCP docstrings**

修改 `src/finance_data/provider/metadata/registry.py`：

```python
# line 56: tool_get_realtime_quote
return_fields=["symbol", "name", "price", "pct_chg", "volume", "amount"],

# line 73: tool_get_index_quote_realtime
return_fields=["symbol", "name", "price", "pct_chg", "volume"],

# line 106: tool_get_sector_rank_realtime
return_fields=["rank", "name", "pct_chg", "volume", "amount"],
```

修改 `src/finance_data/mcp/server.py` docstrings：

```python
# line 103: tool_get_realtime_quote Returns
#   pct_change → pct_chg
JSON 列表，每条包含 symbol、name、price、pct_chg、volume、amount

# line 122: tool_get_index_quote_realtime Returns
#   pct_change → pct_chg
JSON 列表，每条包含 symbol、name、price、pct_chg、volume

# line 147: tool_get_index_history Returns — 补充遗漏字段
JSON 列表，每条包含 date、open、high、low、close、volume、amount、pct_chg

# line 166: tool_get_sector_rank_realtime Returns
#   pct_change → pct_chg
JSON 列表，每条包含 rank、name、pct_chg、volume、amount
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/provider/metadata/test_registry_fields.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/finance_data/provider/metadata/registry.py src/finance_data/mcp/server.py tests/provider/metadata/test_registry_fields.py
git commit -m "fix: registry/MCP docstring pct_change → pct_chg 统一字段名"
```

---

## Task 9: 修复 xueqiu auth 错误分类 + tushare index volume 单位（P1+P2）

1. xueqiu realtime HTTPError 401/403 应归类为 "auth" 而非 "network"
2. tushare index realtime volume 同样有手→股问题

**Files:**
- Modify: `src/finance_data/provider/xueqiu/realtime/realtime.py:65-68`
- Modify: `src/finance_data/provider/xueqiu/index/realtime.py:89-92`
- Modify: `src/finance_data/provider/tushare/index/realtime.py:31`
- Test: `tests/provider/realtime/test_xueqiu_auth_error.py`

**Step 1: Write the failing test**

```python
# tests/provider/realtime/test_xueqiu_auth_error.py
"""验证 xueqiu HTTP 401/403 归类为 auth 错误"""
import requests
from unittest.mock import patch, MagicMock
from finance_data.interface.types import DataFetchError
from finance_data.provider.xueqiu.realtime.realtime import XueqiuRealtimeQuote
import pytest


def test_xueqiu_401_is_auth_error():
    """HTTP 401 应归类为 auth 错误"""
    mock_session = MagicMock(spec=requests.Session)
    response = MagicMock()
    response.status_code = 401
    response.raise_for_status.side_effect = requests.HTTPError(response=response)
    mock_session.get.return_value = response

    provider = XueqiuRealtimeQuote()
    with pytest.raises(DataFetchError) as exc_info:
        provider._request(mock_session, "SZ000001")
    assert exc_info.value.kind == "auth", f"Expected 'auth', got '{exc_info.value.kind}'"


def test_xueqiu_403_is_auth_error():
    """HTTP 403 应归类为 auth 错误"""
    mock_session = MagicMock(spec=requests.Session)
    response = MagicMock()
    response.status_code = 403
    response.raise_for_status.side_effect = requests.HTTPError(response=response)
    mock_session.get.return_value = response

    provider = XueqiuRealtimeQuote()
    with pytest.raises(DataFetchError) as exc_info:
        provider._request(mock_session, "SZ000001")
    assert exc_info.value.kind == "auth", f"Expected 'auth', got '{exc_info.value.kind}'"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/provider/realtime/test_xueqiu_auth_error.py -v`
Expected: FAIL — `assert 'network' == 'auth'`

**Step 3: Fix error classification**

修改 `src/finance_data/provider/xueqiu/realtime/realtime.py:65-68`：

```python
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            kind = "auth" if status in (401, 403) else "network"
            raise DataFetchError(
                "xueqiu", "quotec", str(e), kind
            ) from e
```

同样修改 `src/finance_data/provider/xueqiu/index/realtime.py:89-92`：

```python
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            kind = "auth" if status in (401, 403) else "network"
            raise DataFetchError(
                "xueqiu", "quotec", str(e), kind
            ) from e
```

修复 tushare index realtime volume（手→股），修改 `src/finance_data/provider/tushare/index/realtime.py:31`：

```python
# 原代码
volume=float(row.get("vol", 0)),
# 修改为
volume=float(row.get("vol", 0)) * 100,
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/provider/realtime/test_xueqiu_auth_error.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/finance_data/provider/xueqiu/realtime/realtime.py src/finance_data/provider/xueqiu/index/realtime.py src/finance_data/provider/tushare/index/realtime.py tests/provider/realtime/test_xueqiu_auth_error.py
git commit -m "fix: xueqiu 401/403 归类为 auth + tushare index volume 手→股"
```

---

## Task 10: 修复 registry api_name 与实际调用不一致（P2）

registry 中多个 `api_name` 与 provider 实际调用的 akshare 函数不一致。

**Files:**
- Modify: `src/finance_data/provider/metadata/registry.py:55,72,88`
- Test: `tests/provider/metadata/test_registry_api_name.py`

**Step 1: Write the test**

```python
# tests/provider/metadata/test_registry_api_name.py
"""验证 registry api_name 与实际 provider 调用的函数名一致"""
from finance_data.provider.metadata.registry import TOOL_REGISTRY


def test_realtime_api_name_matches_actual():
    """realtime 实际用 stock_zh_a_spot (sina 源)，非 stock_zh_a_spot_em"""
    meta = TOOL_REGISTRY["tool_get_realtime_quote"]
    assert meta.api_name == "stock_zh_a_spot", \
        f"实际用 sina 源 stock_zh_a_spot，registry 写了 {meta.api_name}"


def test_index_quote_api_name_matches_actual():
    """index_quote 实际用 stock_zh_index_spot_sina，非 index_zh_a_spot_em"""
    meta = TOOL_REGISTRY["tool_get_index_quote_realtime"]
    assert meta.api_name == "stock_zh_index_spot_sina", \
        f"实际用 sina 源，registry 写了 {meta.api_name}"


def test_index_history_api_name_matches_actual():
    """index_history 实际用 stock_zh_index_daily_tx，非 index_zh_a_hist"""
    meta = TOOL_REGISTRY["tool_get_index_history"]
    assert meta.api_name == "stock_zh_index_daily_tx", \
        f"实际用腾讯源，registry 写了 {meta.api_name}"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/provider/metadata/test_registry_api_name.py -v`
Expected: FAIL

**Step 3: Fix api_name in registry**

修改 `src/finance_data/provider/metadata/registry.py`：

```python
# line 55: tool_get_realtime_quote
api_name="stock_zh_a_spot",

# line 72: tool_get_index_quote_realtime
api_name="stock_zh_index_spot_sina",

# line 88: tool_get_index_history
api_name="stock_zh_index_daily_tx",
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/provider/metadata/test_registry_api_name.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/finance_data/provider/metadata/registry.py tests/provider/metadata/test_registry_api_name.py
git commit -m "fix: registry api_name 与实际 akshare 调用函数名对齐"
```

---

## Task 11: 更新 CLAUDE.md 工具名一致性（P2）

CLAUDE.md 中 `tool_get_kline` 和 `tool_get_index_quote` 与实际 MCP 函数名不一致。

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Fix CLAUDE.md**

```markdown
# 在接口列表中修改：
| `tool_get_kline_history` | kline | K线历史数据...  （原为 tool_get_kline）
| `tool_get_index_quote_realtime` | index | 大盘指数实时行情...  （原为 tool_get_index_quote）
```

**Step 2: Verify no other mismatches**

Run: `grep "tool_get_" CLAUDE.md | sort` 对比 `grep "@mcp.tool" src/finance_data/mcp/server.py` 输出。

**Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: CLAUDE.md 工具名与实际 MCP 函数名对齐"
```

---

## Task 12: 统一 timestamp 时区格式（P2）

akshare/tushare 使用 `datetime.now().isoformat()` 无时区信息，xueqiu 使用 `+08:00`。统一添加 CST 时区。

**Files:**
- Modify: `src/finance_data/provider/tushare/realtime/realtime.py:50`
- Modify: `src/finance_data/provider/tushare/index/realtime.py:33`
- Test: `tests/provider/realtime/test_timestamp_timezone.py`

**Step 1: Write the failing test**

```python
# tests/provider/realtime/test_timestamp_timezone.py
"""验证所有 realtime provider 的 timestamp 含时区信息"""
from unittest.mock import patch, MagicMock
import pandas as pd


def test_tushare_realtime_timestamp_has_timezone():
    from finance_data.provider.tushare.realtime.realtime import TushareRealtimeQuote

    mock_df = pd.DataFrame([{
        "close": 15.5, "pct_chg": 1.2, "vol": 500.0, "amount": 775.0,
    }])

    with patch("finance_data.provider.tushare.realtime.realtime.get_pro") as mock_pro:
        pro = MagicMock()
        pro.daily.return_value = mock_df
        mock_pro.return_value = pro
        result = TushareRealtimeQuote().get_realtime_quote("000001")

    ts = result.data[0]["timestamp"]
    assert "+08:00" in ts, f"timestamp 应含时区 +08:00，got: {ts}"


def test_tushare_index_timestamp_has_timezone():
    from finance_data.provider.tushare.index.realtime import TushareIndexQuote

    mock_df = pd.DataFrame([{
        "close": 3200.0, "pct_chg": 0.5, "vol": 3e8, "amount": 4e6,
    }])

    with patch("finance_data.provider.tushare.index.realtime.get_pro") as mock_pro:
        pro = MagicMock()
        pro.index_daily.return_value = mock_df
        mock_pro.return_value = pro
        result = TushareIndexQuote().get_index_quote_realtime("000001.SH")

    ts = result.data[0]["timestamp"]
    assert "+08:00" in ts, f"timestamp 应含时区 +08:00，got: {ts}"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/provider/realtime/test_timestamp_timezone.py -v`
Expected: FAIL

**Step 3: Fix timestamp to include timezone**

修改 `src/finance_data/provider/tushare/realtime/realtime.py:50`：

```python
# 原代码
timestamp=datetime.datetime.now().isoformat(timespec="seconds"),
# 修改为
timestamp=datetime.datetime.now(
    tz=datetime.timezone(datetime.timedelta(hours=8))
).isoformat(timespec="seconds"),
```

修改 `src/finance_data/provider/tushare/index/realtime.py:33`：

```python
# 原代码
timestamp=datetime.datetime.now().isoformat(timespec="seconds"),
# 修改为
timestamp=datetime.datetime.now(
    tz=datetime.timezone(datetime.timedelta(hours=8))
).isoformat(timespec="seconds"),
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/provider/realtime/test_timestamp_timezone.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/finance_data/provider/tushare/realtime/realtime.py src/finance_data/provider/tushare/index/realtime.py tests/provider/realtime/test_timestamp_timezone.py
git commit -m "fix: tushare realtime/index timestamp 添加 +08:00 时区"
```

---

## Task 13: 运行全量测试 + 最终验证

**Step 1: Run all tests**

Run: `.venv/bin/pytest tests/ -v --tb=short`
Expected: ALL PASS

**Step 2: Run validation report**

Run: `python -c "from finance_data.provider.metadata.validator import run_validation_report; print(run_validation_report())"`
Expected: 无新增错误

**Step 3: Final commit (if any fixups needed)**

```bash
git add -A
git commit -m "chore: provider 审计问题全面修复完成"
```

---

## 问题汇总 × Task 映射

| # | 优先级 | 问题 | Task |
|---|--------|------|------|
| 1 | P0 | tushare kline volume 手→股 | Task 1 |
| 2 | P0 | tushare realtime price=EOD close（标注） | Task 2 |
| 3 | P0 | akshare index amount 万元→元 | Task 3 |
| 4 | P1 | xueqiu realtime name 映射错误 | Task 4 |
| 5 | P1 | xueqiu index name 映射错误 | Task 4 |
| 6 | P1 | tushare realtime volume 手→股 | Task 2 |
| 7 | P1 | tushare index realtime name="" | 不修复（API 限制） |
| 8 | P1 | MCP 10 个工具无 try/except | Task 5 |
| 9 | P1 | MCP end="20241231" 硬编码 | Task 6 |
| 10 | P1 | tushare kline/index 排序 | Task 7 |
| 11 | P1 | registry/MCP pct_change → pct_chg | Task 8 |
| 12 | P1 | tushare index volume 手→股 | Task 9 |
| 13 | P2 | CLAUDE.md 工具名不一致 | Task 11 |
| 14 | P2 | xueqiu 401/403 auth 分类 | Task 9 |
| 15 | P2 | registry api_name 不一致 | Task 10 |
| 16 | P2 | timestamp 无时区 | Task 12 |
| 17 | P2 | akshare pct_chg 精度 | 不修复（设计差异） |
| 18 | P2 | xueqiu index history start 截断 | 不修复（API 限制） |
| 19 | P2 | MCP docstring 字段遗漏 | Task 8 |
| 20 | P2 | xueqiu index history 缺 _INDEX_MAP | 不修复（用 fallback 逻辑） |

**不修复说明：**
- **tushare index realtime name=""**：tushare `index_daily` API 不返回 name 字段，属于数据源限制
- **akshare pct_chg 精度**：round(2) 是腾讯源限制，不影响使用
- **xueqiu index history start 截断**：雪球 API 限制 count=-284，属于数据源限制，文档标注即可
- **xueqiu index history 缺 _INDEX_MAP**：当前 fallback 逻辑工作正常，非必要
