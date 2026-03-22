# FinanceData 全量接口接入 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 10 个数据领域（50+ 接口）全量接入 FinanceData，domain-first 目录结构，akshare + tushare 双源，每个接口原子化 migrate → verify → commit。

**Architecture:** Domain-first 目录结构（`provider/kline/`、`provider/realtime/` 等），每个领域独立 models.py + akshare.py + tushare.py。MCP server 每个领域暴露一个 tool，内部 akshare → tushare fallback。

**Tech Stack:** Python 3.14, akshare, tushare, fastmcp, cachetools（realtime TTL 缓存），pytest, pandas

---

## Task 1: 迁移 stock 领域至 domain-first 结构

**Files:**
- Create: `src/finance_data/provider/stock/__init__.py`
- Create: `src/finance_data/provider/stock/models.py` （从 `provider/models.py` 迁移 StockInfo）
- Create: `src/finance_data/provider/stock/akshare.py` （从 `provider/akshare/stock.py` 迁移）
- Create: `src/finance_data/provider/stock/tushare.py` （从 `provider/tushare/stock.py` 迁移）
- Modify: `src/finance_data/mcp/server.py` （更新 import 路径）
- Modify: `tests/provider/test_stock.py` （更新 import 路径）
- Modify: `tests/provider/test_tushare_stock.py` （更新 import 路径）
- Modify: `tests/provider/test_models.py` （更新 import 路径）

**Step 1: 创建 stock 包**

```bash
mkdir -p src/finance_data/provider/stock
```

**Step 2: 创建 stock/models.py（内容与现有 provider/models.py 完全相同）**

```python
# src/finance_data/provider/stock/models.py
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class StockInfo:
    symbol: str
    name: str
    industry: str
    list_date: str
    area: str = ""
    market: str = ""
    city: str = ""
    exchange: str = ""
    ts_code: str = ""
    full_name: str = ""
    established_date: str = ""
    main_business: str = ""
    introduction: str = ""
    chairman: str = ""
    legal_representative: str = ""
    general_manager: str = ""
    secretary: str = ""
    reg_capital: Optional[float] = None
    staff_num: Optional[int] = None
    website: str = ""
    email: str = ""
    reg_address: str = ""
    actual_controller: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name,
            "industry": self.industry, "list_date": self.list_date,
            "area": self.area, "market": self.market, "city": self.city,
            "exchange": self.exchange, "ts_code": self.ts_code,
            "full_name": self.full_name, "established_date": self.established_date,
            "main_business": self.main_business, "introduction": self.introduction,
            "chairman": self.chairman, "legal_representative": self.legal_representative,
            "general_manager": self.general_manager, "secretary": self.secretary,
            "reg_capital": self.reg_capital, "staff_num": self.staff_num,
            "website": self.website, "email": self.email,
            "reg_address": self.reg_address, "actual_controller": self.actual_controller,
        }
```

**Step 3: 创建 stock/__init__.py**

```python
# src/finance_data/provider/stock/__init__.py
```

**Step 4: 复制 akshare.py 和 tushare.py**

将 `provider/akshare/stock.py` 内容复制到 `provider/stock/akshare.py`，更新其中的 import：
```python
# 修改这一行
from finance_data.provider.models import StockInfo
# 改为
from finance_data.provider.stock.models import StockInfo
```

将 `provider/tushare/stock.py` 同理复制到 `provider/stock/tushare.py`，更新 import。

**Step 5: 更新 provider/models.py 为向后兼容 re-export**

```python
# src/finance_data/provider/models.py
# 向后兼容：从新位置 re-export
from finance_data.provider.stock.models import StockInfo  # noqa: F401
```

**Step 6: 更新 server.py import**

```python
# 替换
from finance_data.provider.akshare.stock import get_stock_info as akshare_get_stock_info
from finance_data.provider.tushare.stock import get_stock_info as tushare_get_stock_info
# 改为
from finance_data.provider.stock.akshare import get_stock_info as akshare_get_stock_info
from finance_data.provider.stock.tushare import get_stock_info as tushare_get_stock_info
```

**Step 7: 更新测试 import 路径**

```python
# tests/provider/test_stock.py
from finance_data.provider.stock.akshare import get_stock_info
# tests/provider/test_tushare_stock.py
from finance_data.provider.stock.tushare import get_stock_info
# tests/provider/test_models.py
from finance_data.provider.stock.models import StockInfo
```

**Step 8: 验证**

```bash
.venv/bin/pytest tests/ -v
```
Expected: 28 passed

**Step 9: Commit**

```bash
git add src/finance_data/provider/stock/ src/finance_data/provider/models.py \
        src/finance_data/mcp/server.py tests/provider/
git commit -m "refactor(stock): 迁移至 domain-first 目录结构"
```

---

## Task 2: kline 领域 — models + akshare + tushare + MCP tool

**Files:**
- Create: `src/finance_data/provider/kline/__init__.py`
- Create: `src/finance_data/provider/kline/models.py`
- Create: `src/finance_data/provider/kline/akshare.py`
- Create: `src/finance_data/provider/kline/tushare.py`
- Modify: `src/finance_data/mcp/server.py`
- Create: `tests/provider/kline/__init__.py`
- Create: `tests/provider/kline/test_models.py`
- Create: `tests/provider/kline/test_akshare.py`
- Create: `tests/provider/kline/test_tushare.py`

**Step 1: 写 kline/models.py 的测试（TDD）**

```python
# tests/provider/kline/test_models.py
from finance_data.provider.kline.models import KlineBar

def test_kline_bar_required_fields():
    bar = KlineBar(
        symbol="000001", date="20240101", period="daily",
        open=10.0, high=11.0, low=9.5, close=10.5,
        volume=100000.0, amount=1050000.0, pct_chg=1.5, adj="qfq",
    )
    assert bar.symbol == "000001"
    assert bar.period == "daily"
    assert bar.close == 10.5

def test_kline_bar_to_dict_keys():
    bar = KlineBar(
        symbol="000001", date="20240101", period="daily",
        open=10.0, high=11.0, low=9.5, close=10.5,
        volume=100000.0, amount=1050000.0, pct_chg=1.5, adj="qfq",
    )
    d = bar.to_dict()
    expected = {"symbol","date","period","open","high","low","close",
                "volume","amount","pct_chg","adj"}
    assert set(d.keys()) == expected
```

**Step 2: 实现 kline/models.py**

```python
# src/finance_data/provider/kline/models.py
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class KlineBar:
    symbol: str
    date: str       # YYYYMMDD
    period: str     # daily/weekly/monthly/1min/5min/15min/30min/60min
    open: float
    high: float
    low: float
    close: float
    volume: float   # 手
    amount: float   # 元
    pct_chg: float  # 涨跌幅 %
    adj: str        # qfq/hfq/none

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "date": self.date, "period": self.period,
            "open": self.open, "high": self.high, "low": self.low,
            "close": self.close, "volume": self.volume, "amount": self.amount,
            "pct_chg": self.pct_chg, "adj": self.adj,
        }
```

**Step 3: 写 akshare kline 测试**

```python
# tests/provider/kline/test_akshare.py
from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.kline.akshare import get_kline
from finance_data.provider.types import DataResult, DataFetchError

@pytest.fixture
def mock_daily_df():
    return pd.DataFrame([{
        "日期": "2024-01-01", "开盘": 10.0, "最高": 11.0, "最低": 9.5,
        "收盘": 10.5, "成交量": 100000, "成交额": 1050000.0, "涨跌幅": 1.5,
    }])

def test_get_kline_daily_returns_data_result(mock_daily_df):
    with patch("finance_data.provider.kline.akshare.ak.stock_zh_a_hist",
               return_value=mock_daily_df):
        result = get_kline("000001", period="daily", start="20240101", end="20240101")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1

def test_get_kline_daily_fields(mock_daily_df):
    with patch("finance_data.provider.kline.akshare.ak.stock_zh_a_hist",
               return_value=mock_daily_df):
        result = get_kline("000001", period="daily", start="20240101", end="20240101")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["date"] == "20240101"
    assert row["period"] == "daily"
    assert row["open"] == 10.0
    assert row["close"] == 10.5
    assert row["adj"] == "qfq"

def test_get_kline_network_error():
    with patch("finance_data.provider.kline.akshare.ak.stock_zh_a_hist",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_kline("000001", period="daily", start="20240101", end="20240101")
    assert exc.value.kind == "network"

def test_get_kline_empty_raises_data_error():
    with patch("finance_data.provider.kline.akshare.ak.stock_zh_a_hist",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            get_kline("000001", period="daily", start="20240101", end="20240101")
    assert exc.value.kind == "data"

@pytest.fixture
def mock_min_df():
    return pd.DataFrame([{
        "时间": "2024-01-02 09:31:00", "开盘": 10.0, "最高": 10.2,
        "最低": 9.9, "收盘": 10.1, "成交量": 5000, "成交额": 50500.0, "涨跌幅": 0.5,
    }])

def test_get_kline_1min(mock_min_df):
    with patch("finance_data.provider.kline.akshare.ak.stock_zh_a_hist_min_em",
               return_value=mock_min_df):
        result = get_kline("000001", period="1min", start="20240102", end="20240102")
    assert result.data[0]["period"] == "1min"
    assert result.data[0]["date"] == "20240102"
```

**Step 4: 实现 kline/akshare.py**

```python
# src/finance_data/provider/kline/akshare.py
"""K线历史数据 - akshare"""
import contextlib
import requests
import akshare as ak

from finance_data.provider.kline.models import KlineBar
from finance_data.provider.types import DataResult, DataFetchError

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
    s = str(val).strip()
    return s.replace("-", "").replace(" ", "")[:8]


def get_kline(symbol: str, period: str, start: str, end: str,
              adj: str = "qfq") -> DataResult:
    """
    获取 K线历史数据。

    Args:
        symbol: 股票代码，如 "000001"
        period: daily/weekly/monthly/1min/5min/15min/30min/60min
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD
        adj: qfq（前复权）/ hfq（后复权）/ none

    Returns:
        DataResult，data 为 [KlineBar.to_dict(), ...]
    """
    try:
        with _no_proxy():
            if period in _PERIODS_DAILY:
                df = ak.stock_zh_a_hist(
                    symbol=symbol, period=period,
                    start_date=start, end_date=end, adjust=adj,
                )
            elif period in _PERIODS_MIN:
                df = ak.stock_zh_a_hist_min_em(
                    symbol=symbol, period=_MIN_MAP[period],
                    start_date=start, end_date=end, adjust=adj,
                )
            else:
                raise DataFetchError("akshare", "get_kline",
                                     f"不支持的 period: {period}", "data")
    except DataFetchError:
        raise
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "get_kline", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "get_kline", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "get_kline",
                             f"无数据: {symbol} {period} {start}-{end}", "data")

    bars = []
    for _, row in df.iterrows():
        date_col = "时间" if period in _PERIODS_MIN else "日期"
        bars.append(KlineBar(
            symbol=symbol,
            date=_parse_date(row.get(date_col, "")),
            period=period,
            open=float(row.get("开盘", 0)),
            high=float(row.get("最高", 0)),
            low=float(row.get("最低", 0)),
            close=float(row.get("收盘", 0)),
            volume=float(row.get("成交量", 0)),
            amount=float(row.get("成交额", 0)),
            pct_chg=float(row.get("涨跌幅", 0)),
            adj=adj,
        ).to_dict())

    return DataResult(
        data=bars, source="akshare",
        meta={"rows": len(bars), "symbol": symbol, "period": period},
    )
```

**Step 5: 写 tushare kline 测试**

```python
# tests/provider/kline/test_tushare.py
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from finance_data.provider.kline.tushare import get_kline
from finance_data.provider.types import DataResult, DataFetchError

@pytest.fixture
def mock_pro():
    return MagicMock()

@pytest.fixture
def mock_daily_df():
    return pd.DataFrame([{
        "trade_date": "20240101", "open": 10.0, "high": 11.0,
        "low": 9.5, "close": 10.5, "vol": 100000.0,
        "amount": 1050000.0, "pct_chg": 1.5,
    }])

def test_get_kline_daily_returns_data_result(mock_pro, mock_daily_df):
    mock_pro.daily.return_value = mock_daily_df
    with patch("finance_data.provider.kline.tushare._get_pro", return_value=mock_pro):
        result = get_kline("000001", period="daily", start="20240101", end="20240101")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"

def test_get_kline_daily_fields(mock_pro, mock_daily_df):
    mock_pro.daily.return_value = mock_daily_df
    with patch("finance_data.provider.kline.tushare._get_pro", return_value=mock_pro):
        result = get_kline("000001", period="daily", start="20240101", end="20240101")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["date"] == "20240101"
    assert row["close"] == 10.5
    assert row["adj"] == "qfq"

def test_get_kline_empty_raises(mock_pro):
    mock_pro.daily.return_value = pd.DataFrame()
    with patch("finance_data.provider.kline.tushare._get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            get_kline("INVALID", period="daily", start="20240101", end="20240101")
    assert exc.value.kind == "data"

def test_get_kline_network_error(mock_pro):
    mock_pro.daily.side_effect = ConnectionError("timeout")
    with patch("finance_data.provider.kline.tushare._get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            get_kline("000001", period="daily", start="20240101", end="20240101")
    assert exc.value.kind == "network"

def test_get_kline_weekly(mock_pro):
    df = pd.DataFrame([{
        "trade_date": "20240101", "open": 10.0, "high": 11.0,
        "low": 9.5, "close": 10.5, "vol": 500000.0, "amount": 5000000.0, "pct_chg": 2.0,
    }])
    mock_pro.weekly.return_value = df
    with patch("finance_data.provider.kline.tushare._get_pro", return_value=mock_pro):
        result = get_kline("000001", period="weekly", start="20240101", end="20240101")
    assert result.data[0]["period"] == "weekly"
```

**Step 6: 实现 kline/tushare.py**

```python
# src/finance_data/provider/kline/tushare.py
"""K线历史数据 - tushare"""
import os
import tushare as ts

from finance_data.provider.kline.models import KlineBar
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)
_DAILY_FUNC = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
_MIN_FREQ = {"1min": "1min", "5min": "5min", "15min": "15min",
             "30min": "30min", "60min": "60min"}


def _get_pro():
    token = os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        raise DataFetchError("tushare", "init", "TUSHARE_TOKEN 未设置", "auth")
    pro = ts.pro_api(token=token)
    api_url = os.environ.get("TUSHARE_API_URL", "")
    if api_url:
        pro._DataApi__token = token
        pro._DataApi__http_url = api_url
    return pro


def _ts_code(symbol: str) -> str:
    if "." in symbol:
        return symbol
    return f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"


def get_kline(symbol: str, period: str, start: str, end: str,
              adj: str = "qfq") -> DataResult:
    pro = _get_pro()
    ts_code = _ts_code(symbol)
    adj_ts = {"qfq": "qfq", "hfq": "hfq", "none": ""}.get(adj, "qfq")

    try:
        if period in _DAILY_FUNC:
            fn = getattr(pro, _DAILY_FUNC[period])
            df = fn(ts_code=ts_code, start_date=start, end_date=end,
                    fields="trade_date,open,high,low,close,vol,amount,pct_chg")
        elif period in _MIN_FREQ:
            df = pro.stk_mins(ts_code=ts_code, freq=_MIN_FREQ[period],
                              start_date=start + " 09:00:00",
                              end_date=end + " 15:30:00")
        else:
            raise DataFetchError("tushare", "get_kline",
                                 f"不支持的 period: {period}", "data")
    except DataFetchError:
        raise
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "get_kline", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "get_kline", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "get_kline",
                             f"无数据: {symbol} {period} {start}-{end}", "data")

    date_col = "trade_time" if period in _MIN_FREQ else "trade_date"
    bars = []
    for _, row in df.iterrows():
        raw_date = str(row.get(date_col, "")).replace("-", "").replace(" ", "")[:8]
        bars.append(KlineBar(
            symbol=symbol,
            date=raw_date,
            period=period,
            open=float(row.get("open", 0)),
            high=float(row.get("high", 0)),
            low=float(row.get("low", 0)),
            close=float(row.get("close", 0)),
            volume=float(row.get("vol", 0)),
            amount=float(row.get("amount", 0)),
            pct_chg=float(row.get("pct_chg", 0)),
            adj=adj,
        ).to_dict())

    return DataResult(
        data=bars, source="tushare",
        meta={"rows": len(bars), "symbol": symbol, "period": period},
    )
```

**Step 7: 更新 server.py，添加 tool_get_kline**

在 server.py 现有 tool 之后追加：

```python
from finance_data.provider.kline.akshare import get_kline as akshare_get_kline
from finance_data.provider.kline.tushare import get_kline as tushare_get_kline

@mcp.tool()
async def tool_get_kline(
    symbol: str,
    period: str = "daily",
    start: str = "20240101",
    end: str = "20241231",
    adj: str = "qfq",
) -> str:
    """
    获取 K线历史数据。

    Args:
        symbol: 股票代码，如 "000001"
        period: daily/weekly/monthly/1min/5min/15min/30min/60min
        start: 开始日期 YYYYMMDD
        end: 结束日期 YYYYMMDD
        adj: qfq（前复权）/ hfq（后复权）/ none
    """
    providers = [
        ("akshare", akshare_get_kline),
        ("tushare", tushare_get_kline),
    ]
    errors = []
    for name, fn in providers:
        try:
            return _to_json(fn(symbol, period=period, start=start, end=end, adj=adj))
        except Exception as e:
            logger.warning(f"{name} get_kline 失败: {e}")
            errors.append(str(e))
    return json.dumps({"error": f"所有数据源均失败: {errors}"}, ensure_ascii=False)
```

**Step 8: 验证**

```bash
.venv/bin/pytest tests/ -v
```
Expected: 全部通过

**Step 9: Commit**

```bash
git add src/finance_data/provider/kline/ tests/provider/kline/ src/finance_data/mcp/server.py
git commit -m "feat(kline): 接入 K线历史接口 (akshare+tushare)"
```

---

## Task 3: realtime 领域 — 实时行情 + TTL 缓存

**Files:**
- Create: `src/finance_data/provider/realtime/__init__.py`
- Create: `src/finance_data/provider/realtime/models.py`
- Create: `src/finance_data/provider/realtime/cache.py`
- Create: `src/finance_data/provider/realtime/akshare.py`
- Create: `src/finance_data/provider/realtime/tushare.py`
- Modify: `src/finance_data/mcp/server.py`
- Create: `tests/provider/realtime/test_models.py`
- Create: `tests/provider/realtime/test_akshare.py`
- Create: `tests/provider/realtime/test_tushare.py`

**Step 1: 先安装 cachetools**

```bash
# 确认 pyproject.toml dependencies 包含 cachetools，若无则添加
grep cachetools pyproject.toml || echo "需要添加 cachetools 到依赖"
```

如果缺失，在 pyproject.toml `dependencies` 中添加 `"cachetools>=5.0"` 后执行：
```bash
.venv/bin/pip install cachetools
```

**Step 2: 写 models 测试**

```python
# tests/provider/realtime/test_models.py
from finance_data.provider.realtime.models import RealtimeQuote

def test_realtime_quote_required_fields():
    q = RealtimeQuote(
        symbol="000001", name="平安银行", price=12.5, pct_chg=1.2,
        volume=1000000.0, amount=12500000.0,
        market_cap=None, pe=None, pb=None, turnover_rate=None,
        timestamp="2024-01-02T10:00:00",
    )
    assert q.symbol == "000001"
    assert q.price == 12.5

def test_realtime_quote_to_dict_keys():
    q = RealtimeQuote(
        symbol="000001", name="平安银行", price=12.5, pct_chg=1.2,
        volume=1000000.0, amount=12500000.0,
        market_cap=None, pe=None, pb=None, turnover_rate=None,
        timestamp="2024-01-02T10:00:00",
    )
    d = q.to_dict()
    assert set(d.keys()) == {
        "symbol","name","price","pct_chg","volume","amount",
        "market_cap","pe","pb","turnover_rate","timestamp",
    }
```

**Step 3: 实现 realtime/models.py**

```python
# src/finance_data/provider/realtime/models.py
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RealtimeQuote:
    symbol: str
    name: str
    price: float
    pct_chg: float
    volume: float
    amount: float
    market_cap: Optional[float]
    pe: Optional[float]
    pb: Optional[float]
    turnover_rate: Optional[float]
    timestamp: str  # ISO 8601

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol, "name": self.name,
            "price": self.price, "pct_chg": self.pct_chg,
            "volume": self.volume, "amount": self.amount,
            "market_cap": self.market_cap, "pe": self.pe,
            "pb": self.pb, "turnover_rate": self.turnover_rate,
            "timestamp": self.timestamp,
        }
```

**Step 4: 实现 realtime/cache.py**

```python
# src/finance_data/provider/realtime/cache.py
from cachetools import TTLCache

# 实时行情缓存：最多 512 支股票，20 分钟 TTL
_quote_cache: TTLCache = TTLCache(maxsize=512, ttl=1200)


def get_cached(key: str):
    return _quote_cache.get(key)


def set_cached(key: str, value) -> None:
    _quote_cache[key] = value
```

**Step 5: 写 akshare realtime 测试**

```python
# tests/provider/realtime/test_akshare.py
from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.realtime.akshare import get_realtime_quote
from finance_data.provider.realtime import cache
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture(autouse=True)
def clear_cache():
    cache._quote_cache.clear()
    yield
    cache._quote_cache.clear()


@pytest.fixture
def mock_spot_df():
    return pd.DataFrame([{
        "代码": "000001", "名称": "平安银行",
        "最新价": 12.5, "涨跌幅": 1.2,
        "成交量": 1000000, "成交额": 12500000.0,
        "总市值": 2420000000000.0, "市盈率-动态": 6.5, "市净率": 0.8,
        "换手率": 0.52,
    }])


def test_get_realtime_quote_returns_data_result(mock_spot_df):
    with patch("finance_data.provider.realtime.akshare.ak.stock_zh_a_spot_em",
               return_value=mock_spot_df):
        result = get_realtime_quote("000001")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"


def test_get_realtime_quote_fields(mock_spot_df):
    with patch("finance_data.provider.realtime.akshare.ak.stock_zh_a_spot_em",
               return_value=mock_spot_df):
        result = get_realtime_quote("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["name"] == "平安银行"
    assert row["price"] == 12.5
    assert row["pct_chg"] == 1.2


def test_get_realtime_quote_cache_hit(mock_spot_df):
    call_count = 0
    def mock_spot(*a, **kw):
        nonlocal call_count
        call_count += 1
        return mock_spot_df

    with patch("finance_data.provider.realtime.akshare.ak.stock_zh_a_spot_em",
               side_effect=mock_spot):
        get_realtime_quote("000001")
        get_realtime_quote("000001")  # 命中缓存
    assert call_count == 1  # akshare 只被调用一次


def test_get_realtime_quote_network_error():
    with patch("finance_data.provider.realtime.akshare.ak.stock_zh_a_spot_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_realtime_quote("000001")
    assert exc.value.kind == "network"
```

**Step 6: 实现 realtime/akshare.py**

```python
# src/finance_data/provider/realtime/akshare.py
"""实时行情 - akshare（含 TTL 缓存）"""
import contextlib
import datetime
import requests
import akshare as ak

from finance_data.provider.realtime.models import RealtimeQuote
from finance_data.provider.realtime import cache
from finance_data.provider.types import DataResult, DataFetchError

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


def _opt_float(val) -> float | None:
    try:
        v = float(val)
        return None if v != v else v  # NaN check
    except (TypeError, ValueError):
        return None


def get_realtime_quote(symbol: str) -> DataResult:
    """获取实时行情（TTL 缓存 20 分钟）。"""
    cache_key = f"akshare:realtime:{symbol}"
    cached = cache.get_cached(cache_key)
    if cached is not None:
        return cached

    try:
        with _no_proxy():
            df = ak.stock_zh_a_spot_em()
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_zh_a_spot_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_zh_a_spot_em", str(e), "data") from e

    row_df = df[df["代码"] == symbol]
    if row_df.empty:
        raise DataFetchError("akshare", "stock_zh_a_spot_em",
                             f"未找到股票: {symbol}", "data")

    row = row_df.iloc[0]
    quote = RealtimeQuote(
        symbol=symbol,
        name=str(row.get("名称", "")),
        price=float(row.get("最新价", 0)),
        pct_chg=float(row.get("涨跌幅", 0)),
        volume=float(row.get("成交量", 0)),
        amount=float(row.get("成交额", 0)),
        market_cap=_opt_float(row.get("总市值")),
        pe=_opt_float(row.get("市盈率-动态")),
        pb=_opt_float(row.get("市净率")),
        turnover_rate=_opt_float(row.get("换手率")),
        timestamp=datetime.datetime.now().isoformat(timespec="seconds"),
    )
    result = DataResult(
        data=[quote.to_dict()], source="akshare",
        meta={"rows": 1, "symbol": symbol},
    )
    cache.set_cached(cache_key, result)
    return result
```

**Step 7: 实现 realtime/tushare.py**

```python
# src/finance_data/provider/realtime/tushare.py
"""实时行情 - tushare"""
import datetime
import os
import tushare as ts

from finance_data.provider.realtime.models import RealtimeQuote
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _get_pro():
    token = os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        raise DataFetchError("tushare", "init", "TUSHARE_TOKEN 未设置", "auth")
    pro = ts.pro_api(token=token)
    api_url = os.environ.get("TUSHARE_API_URL", "")
    if api_url:
        pro._DataApi__token = token
        pro._DataApi__http_url = api_url
    return pro


def _ts_code(symbol: str) -> str:
    if "." in symbol:
        return symbol
    return f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"


def _opt_float(val):
    try:
        v = float(val)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def get_realtime_quote(symbol: str) -> DataResult:
    """获取实时行情（tushare daily 最新一条作为近实时数据）。"""
    pro = _get_pro()
    ts_code = _ts_code(symbol)
    try:
        df = pro.daily(ts_code=ts_code, limit=1)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "daily", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "daily", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "daily", f"未找到股票: {symbol}", "data")

    row = df.iloc[0]
    quote = RealtimeQuote(
        symbol=symbol,
        name="",  # tushare daily 不含股票名称
        price=float(row.get("close", 0)),
        pct_chg=float(row.get("pct_chg", 0)),
        volume=float(row.get("vol", 0)),
        amount=float(row.get("amount", 0)),
        market_cap=None,
        pe=None,
        pb=None,
        turnover_rate=None,
        timestamp=datetime.datetime.now().isoformat(timespec="seconds"),
    )
    return DataResult(
        data=[quote.to_dict()], source="tushare",
        meta={"rows": 1, "symbol": symbol},
    )
```

**Step 8: 添加 MCP tool**

在 server.py 追加：

```python
from finance_data.provider.realtime.akshare import get_realtime_quote as akshare_get_realtime
from finance_data.provider.realtime.tushare import get_realtime_quote as tushare_get_realtime

@mcp.tool()
async def tool_get_realtime_quote(symbol: str) -> str:
    """
    获取股票实时行情（含 20 分钟缓存）。

    Args:
        symbol: 股票代码，如 "000001"
    """
    providers = [("akshare", akshare_get_realtime), ("tushare", tushare_get_realtime)]
    errors = []
    for name, fn in providers:
        try:
            return _to_json(fn(symbol))
        except Exception as e:
            logger.warning(f"{name} get_realtime_quote 失败: {e}")
            errors.append(str(e))
    return json.dumps({"error": f"所有数据源均失败: {errors}"}, ensure_ascii=False)
```

**Step 9: 验证**

```bash
.venv/bin/pytest tests/ -v
```

**Step 10: Commit**

```bash
git add src/finance_data/provider/realtime/ tests/provider/realtime/ src/finance_data/mcp/server.py
git commit -m "feat(realtime): 接入实时行情接口，含 TTL 缓存"
```

---

## Task 4: index 领域 — 大盘指数行情

**Files:**
- Create: `src/finance_data/provider/index/` (models, akshare, tushare, __init__)
- Create: `tests/provider/index/` (test_models, test_akshare, test_tushare)
- Modify: `src/finance_data/mcp/server.py`

**Step 1: 写 models 测试**

```python
# tests/provider/index/test_models.py
from finance_data.provider.index.models import IndexQuote, IndexBar

def test_index_quote_to_dict_keys():
    q = IndexQuote(symbol="000001.SH", name="上证指数",
                   price=3100.0, pct_chg=0.5, volume=1e10,
                   amount=1e12, timestamp="2024-01-02T15:00:00")
    d = q.to_dict()
    assert set(d.keys()) == {"symbol","name","price","pct_chg","volume","amount","timestamp"}

def test_index_bar_to_dict_keys():
    b = IndexBar(symbol="000001.SH", date="20240102",
                 open=3090.0, high=3110.0, low=3085.0, close=3100.0,
                 volume=1e10, amount=1e12, pct_chg=0.5)
    d = b.to_dict()
    assert set(d.keys()) == {"symbol","date","open","high","low","close","volume","amount","pct_chg"}
```

**Step 2: 实现 index/models.py**

```python
# src/finance_data/provider/index/models.py
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class IndexQuote:
    symbol: str     # 000001.SH
    name: str
    price: float
    pct_chg: float
    volume: float
    amount: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "name": self.name,
                "price": self.price, "pct_chg": self.pct_chg,
                "volume": self.volume, "amount": self.amount,
                "timestamp": self.timestamp}


@dataclass
class IndexBar:
    symbol: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    pct_chg: float

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "date": self.date,
                "open": self.open, "high": self.high, "low": self.low,
                "close": self.close, "volume": self.volume,
                "amount": self.amount, "pct_chg": self.pct_chg}
```

**Step 3: 写 akshare index 测试**

```python
# tests/provider/index/test_akshare.py
from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.index.akshare import get_index_quote, get_index_history
from finance_data.provider.types import DataResult, DataFetchError

@pytest.fixture
def mock_index_df():
    return pd.DataFrame([{
        "代码": "000001", "名称": "上证指数",
        "最新价": 3100.0, "涨跌幅": 0.5,
        "成交量": 1e10, "成交额": 1e12,
    }])

def test_get_index_quote_returns_data_result(mock_index_df):
    with patch("finance_data.provider.index.akshare.ak.stock_zh_index_spot_sina",
               return_value=mock_index_df):
        result = get_index_quote("000001.SH")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"

def test_get_index_quote_fields(mock_index_df):
    with patch("finance_data.provider.index.akshare.ak.stock_zh_index_spot_sina",
               return_value=mock_index_df):
        result = get_index_quote("000001.SH")
    row = result.data[0]
    assert row["symbol"] == "000001.SH"
    assert row["price"] == 3100.0

@pytest.fixture
def mock_hist_df():
    return pd.DataFrame([{
        "日期": "2024-01-02", "开盘": 3090.0, "最高": 3110.0,
        "最低": 3085.0, "收盘": 3100.0, "成交量": 1e10,
        "成交额": 1e12, "涨跌幅": 0.5,
    }])

def test_get_index_history_returns_data_result(mock_hist_df):
    with patch("finance_data.provider.index.akshare.ak.stock_zh_index_daily_em",
               return_value=mock_hist_df):
        result = get_index_history("000001.SH", start="20240101", end="20240102")
    assert isinstance(result, DataResult)
    assert result.data[0]["close"] == 3100.0
```

**Step 4: 实现 index/akshare.py**

```python
# src/finance_data/provider/index/akshare.py
"""大盘指数 - akshare"""
import contextlib
import datetime
import requests
import akshare as ak

from finance_data.provider.index.models import IndexQuote, IndexBar
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)
# 将 000001.SH 转为 sh000001
_INDEX_MAP = {"000001.SH": "000001", "399001.SZ": "399001",
              "399006.SZ": "399006", "000300.SH": "000300",
              "000016.SH": "000016", "000905.SH": "000905"}


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


def _strip_code(symbol: str) -> str:
    """000001.SH → 000001"""
    return symbol.split(".")[0]


def get_index_quote(symbol: str) -> DataResult:
    """获取大盘指数实时行情。"""
    code = _strip_code(symbol)
    try:
        with _no_proxy():
            df = ak.stock_zh_index_spot_sina()
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_zh_index_spot_sina", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_zh_index_spot_sina", str(e), "data") from e

    row_df = df[df["代码"] == code]
    if row_df.empty:
        raise DataFetchError("akshare", "stock_zh_index_spot_sina",
                             f"未找到指数: {symbol}", "data")
    row = row_df.iloc[0]
    quote = IndexQuote(
        symbol=symbol,
        name=str(row.get("名称", "")),
        price=float(row.get("最新价", 0)),
        pct_chg=float(row.get("涨跌幅", 0)),
        volume=float(row.get("成交量", 0)),
        amount=float(row.get("成交额", 0)),
        timestamp=datetime.datetime.now().isoformat(timespec="seconds"),
    )
    return DataResult(data=[quote.to_dict()], source="akshare",
                      meta={"rows": 1, "symbol": symbol})


def get_index_history(symbol: str, start: str, end: str) -> DataResult:
    """获取大盘指数历史 K线。"""
    code = _strip_code(symbol)
    try:
        with _no_proxy():
            df = ak.stock_zh_index_daily_em(symbol=f"sh{code}" if symbol.endswith(".SH") else f"sz{code}")
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_zh_index_daily_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_zh_index_daily_em", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_zh_index_daily_em",
                             f"无数据: {symbol}", "data")

    df = df[(df["日期"] >= start[:4] + "-" + start[4:6] + "-" + start[6:]) &
            (df["日期"] <= end[:4] + "-" + end[4:6] + "-" + end[6:])]

    bars = [IndexBar(
        symbol=symbol,
        date=str(row["日期"]).replace("-", ""),
        open=float(row.get("开盘", 0)),
        high=float(row.get("最高", 0)),
        low=float(row.get("最低", 0)),
        close=float(row.get("收盘", 0)),
        volume=float(row.get("成交量", 0)),
        amount=float(row.get("成交额", 0)),
        pct_chg=float(row.get("涨跌幅", 0)),
    ).to_dict() for _, row in df.iterrows()]

    return DataResult(data=bars, source="akshare",
                      meta={"rows": len(bars), "symbol": symbol})
```

**Step 5: 实现 index/tushare.py（参考 kline/tushare.py 模式，使用 pro.index_daily()）**

```python
# src/finance_data/provider/index/tushare.py
"""大盘指数 - tushare"""
import datetime, os
import tushare as ts
from finance_data.provider.index.models import IndexQuote, IndexBar
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _get_pro():
    token = os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        raise DataFetchError("tushare", "init", "TUSHARE_TOKEN 未设置", "auth")
    pro = ts.pro_api(token=token)
    api_url = os.environ.get("TUSHARE_API_URL", "")
    if api_url:
        pro._DataApi__token = token
        pro._DataApi__http_url = api_url
    return pro


def get_index_quote(symbol: str) -> DataResult:
    """获取指数最新行情（取 daily 最近一条）。"""
    pro = _get_pro()
    try:
        df = pro.index_daily(ts_code=symbol, limit=1)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "index_daily", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "index_daily", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "index_daily", f"未找到指数: {symbol}", "data")

    row = df.iloc[0]
    quote = IndexQuote(
        symbol=symbol, name="",
        price=float(row.get("close", 0)),
        pct_chg=float(row.get("pct_chg", 0)),
        volume=float(row.get("vol", 0)),
        amount=float(row.get("amount", 0)),
        timestamp=datetime.datetime.now().isoformat(timespec="seconds"),
    )
    return DataResult(data=[quote.to_dict()], source="tushare",
                      meta={"rows": 1, "symbol": symbol})


def get_index_history(symbol: str, start: str, end: str) -> DataResult:
    """获取指数历史 K线。"""
    pro = _get_pro()
    try:
        df = pro.index_daily(ts_code=symbol, start_date=start, end_date=end)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "index_daily", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "index_daily", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "index_daily",
                             f"无数据: {symbol} {start}-{end}", "data")

    bars = [IndexBar(
        symbol=symbol,
        date=str(row.get("trade_date", "")),
        open=float(row.get("open", 0)), high=float(row.get("high", 0)),
        low=float(row.get("low", 0)), close=float(row.get("close", 0)),
        volume=float(row.get("vol", 0)), amount=float(row.get("amount", 0)),
        pct_chg=float(row.get("pct_chg", 0)),
    ).to_dict() for _, row in df.iterrows()]

    return DataResult(data=bars, source="tushare",
                      meta={"rows": len(bars), "symbol": symbol})
```

**Step 6: 添加 MCP tools（2 个：行情 + 历史）**

```python
from finance_data.provider.index.akshare import (
    get_index_quote as ak_index_quote,
    get_index_history as ak_index_history,
)
from finance_data.provider.index.tushare import (
    get_index_quote as ts_index_quote,
    get_index_history as ts_index_history,
)

@mcp.tool()
async def tool_get_index_quote(symbol: str = "000001.SH") -> str:
    """获取大盘指数实时行情。symbol 如 000001.SH / 399001.SZ"""
    providers = [("akshare", ak_index_quote), ("tushare", ts_index_quote)]
    errors = []
    for name, fn in providers:
        try:
            return _to_json(fn(symbol))
        except Exception as e:
            logger.warning(f"{name} get_index_quote 失败: {e}")
            errors.append(str(e))
    return json.dumps({"error": f"所有数据源均失败: {errors}"}, ensure_ascii=False)

@mcp.tool()
async def tool_get_index_history(
    symbol: str = "000001.SH",
    start: str = "20240101",
    end: str = "20241231",
) -> str:
    """获取大盘指数历史 K线。symbol 如 000001.SH / 399001.SZ"""
    providers = [("akshare", ak_index_history), ("tushare", ts_index_history)]
    errors = []
    for name, fn in providers:
        try:
            return _to_json(fn(symbol, start=start, end=end))
        except Exception as e:
            logger.warning(f"{name} get_index_history 失败: {e}")
            errors.append(str(e))
    return json.dumps({"error": f"所有数据源均失败: {errors}"}, ensure_ascii=False)
```

**Step 7: 验证 & Commit**

```bash
.venv/bin/pytest tests/ -v
git add src/finance_data/provider/index/ tests/provider/index/ src/finance_data/mcp/server.py
git commit -m "feat(index): 接入大盘指数接口 (akshare+tushare)"
```

---

## Task 5: sector 领域 — 行业板块排名

**Files:**
- Create: `src/finance_data/provider/sector/` (models, akshare, tushare, __init__)
- Create: `tests/provider/sector/`
- Modify: `src/finance_data/mcp/server.py`

**Step 1: 写 sector 测试**

```python
# tests/provider/sector/test_akshare.py
from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.sector.akshare import get_sector_rank
from finance_data.provider.types import DataResult, DataFetchError

@pytest.fixture
def mock_sector_df():
    return pd.DataFrame([{
        "板块名称": "银行", "涨跌幅": 1.2,
        "领涨股票": "招商银行", "领涨股票-涨跌幅": 3.5,
        "上涨家数": 35, "下跌家数": 5,
    }])

def test_get_sector_rank_returns_data_result(mock_sector_df):
    with patch("finance_data.provider.sector.akshare.ak.stock_board_industry_name_em",
               return_value=mock_sector_df):
        result = get_sector_rank()
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1

def test_get_sector_rank_fields(mock_sector_df):
    with patch("finance_data.provider.sector.akshare.ak.stock_board_industry_name_em",
               return_value=mock_sector_df):
        result = get_sector_rank()
    row = result.data[0]
    assert row["name"] == "银行"
    assert row["pct_chg"] == 1.2
    assert row["leader_stock"] == "招商银行"
```

**Step 2: 实现 sector/models.py**

```python
# src/finance_data/provider/sector/models.py
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SectorRank:
    name: str
    pct_chg: float
    leader_stock: str
    leader_pct_chg: float
    up_count: Optional[int] = None
    down_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "pct_chg": self.pct_chg,
                "leader_stock": self.leader_stock,
                "leader_pct_chg": self.leader_pct_chg,
                "up_count": self.up_count, "down_count": self.down_count}
```

**Step 3: 实现 sector/akshare.py**

```python
# src/finance_data/provider/sector/akshare.py
import contextlib, requests
import akshare as ak
from finance_data.provider.sector.models import SectorRank
from finance_data.provider.types import DataResult, DataFetchError

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


def _opt_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def get_sector_rank() -> DataResult:
    """获取行业板块涨跌排名。"""
    try:
        with _no_proxy():
            df = ak.stock_board_industry_name_em()
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_board_industry_name_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_board_industry_name_em", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_board_industry_name_em", "无数据", "data")

    rows = [SectorRank(
        name=str(r.get("板块名称", "")),
        pct_chg=float(r.get("涨跌幅", 0)),
        leader_stock=str(r.get("领涨股票", "")),
        leader_pct_chg=float(r.get("领涨股票-涨跌幅", 0)),
        up_count=_opt_int(r.get("上涨家数")),
        down_count=_opt_int(r.get("下跌家数")),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="akshare", meta={"rows": len(rows)})
```

**Step 4: 实现 sector/tushare.py（tushare 无直接行业排名接口，降级为仅返回 akshare）**

```python
# src/finance_data/provider/sector/tushare.py
"""行业板块排名 - tushare 暂无对应接口，此文件保留结构但抛出 data 错误"""
from finance_data.provider.types import DataResult, DataFetchError


def get_sector_rank() -> DataResult:
    raise DataFetchError("tushare", "get_sector_rank",
                         "tushare 无行业板块排名接口", "data")
```

**Step 5: 添加 MCP tool**

```python
from finance_data.provider.sector.akshare import get_sector_rank as ak_sector_rank
from finance_data.provider.sector.tushare import get_sector_rank as ts_sector_rank

@mcp.tool()
async def tool_get_sector_rank() -> str:
    """获取行业板块涨跌排名（按涨跌幅排序）。"""
    providers = [("akshare", ak_sector_rank), ("tushare", ts_sector_rank)]
    errors = []
    for name, fn in providers:
        try:
            return _to_json(fn())
        except Exception as e:
            logger.warning(f"{name} get_sector_rank 失败: {e}")
            errors.append(str(e))
    return json.dumps({"error": f"所有数据源均失败: {errors}"}, ensure_ascii=False)
```

**Step 6: 验证 & Commit**

```bash
.venv/bin/pytest tests/ -v
git add src/finance_data/provider/sector/ tests/provider/sector/ src/finance_data/mcp/server.py
git commit -m "feat(sector): 接入行业板块排名接口"
```

---

## Task 6: chip 领域 — 筹码分布（仅 akshare）

**Files:**
- Create: `src/finance_data/provider/chip/` (models, akshare, __init__)
- Create: `tests/provider/chip/`
- Modify: `src/finance_data/mcp/server.py`

**Step 1: 写测试**

```python
# tests/provider/chip/test_akshare.py
from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.chip.akshare import get_chip_distribution
from finance_data.provider.types import DataResult, DataFetchError

@pytest.fixture
def mock_chip_df():
    return pd.DataFrame([{
        "日期": "2024-01-02",
        "获利比例": 55.3, "平均成本": 11.8,
        "90成本-低": 8.5, "90成本-高": 14.2, "集中度": 62.1,
    }])

def test_get_chip_distribution_returns_data_result(mock_chip_df):
    with patch("finance_data.provider.chip.akshare.ak.stock_cyq_em",
               return_value=mock_chip_df):
        result = get_chip_distribution("000001")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"

def test_get_chip_distribution_fields(mock_chip_df):
    with patch("finance_data.provider.chip.akshare.ak.stock_cyq_em",
               return_value=mock_chip_df):
        result = get_chip_distribution("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["profit_ratio"] == 55.3
    assert row["avg_cost"] == 11.8
    assert row["concentration"] == 62.1
```

**Step 2: 实现 chip/models.py**

```python
# src/finance_data/provider/chip/models.py
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ChipDistribution:
    symbol: str
    date: str
    avg_cost: float
    concentration: float    # 筹码集中度 %
    profit_ratio: float     # 获利比例 %
    cost_90: float          # 90% 筹码成本区间上沿
    cost_10: float          # 下沿

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "date": self.date,
                "avg_cost": self.avg_cost, "concentration": self.concentration,
                "profit_ratio": self.profit_ratio,
                "cost_90": self.cost_90, "cost_10": self.cost_10}
```

**Step 3: 实现 chip/akshare.py**

```python
# src/finance_data/provider/chip/akshare.py
import contextlib, requests
import akshare as ak
from finance_data.provider.chip.models import ChipDistribution
from finance_data.provider.types import DataResult, DataFetchError

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


def get_chip_distribution(symbol: str, adjust: str = "") -> DataResult:
    """获取筹码分布（最近 N 日）。"""
    try:
        with _no_proxy():
            df = ak.stock_cyq_em(symbol=symbol, adjust=adjust)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_cyq_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_cyq_em", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_cyq_em", f"无数据: {symbol}", "data")

    rows = [ChipDistribution(
        symbol=symbol,
        date=str(r.get("日期", "")).replace("-", ""),
        avg_cost=float(r.get("平均成本", 0)),
        concentration=float(r.get("集中度", 0)),
        profit_ratio=float(r.get("获利比例", 0)),
        cost_90=float(r.get("90成本-高", 0)),
        cost_10=float(r.get("90成本-低", 0)),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="akshare",
                      meta={"rows": len(rows), "symbol": symbol})
```

**Step 4: MCP tool**

```python
from finance_data.provider.chip.akshare import get_chip_distribution as ak_chip

@mcp.tool()
async def tool_get_chip_distribution(symbol: str) -> str:
    """获取个股筹码分布（获利比例、平均成本、集中度）。"""
    try:
        return _to_json(ak_chip(symbol))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
```

**Step 5: 验证 & Commit**

```bash
.venv/bin/pytest tests/ -v
git add src/finance_data/provider/chip/ tests/provider/chip/ src/finance_data/mcp/server.py
git commit -m "feat(chip): 接入筹码分布接口 (akshare)"
```

---

## Task 7: fundamental 领域 — 财务基本面

**Files:**
- Create: `src/finance_data/provider/fundamental/` (models, akshare, tushare, __init__)
- Create: `tests/provider/fundamental/`
- Modify: `src/finance_data/mcp/server.py`

**Step 1: 实现 fundamental/models.py**

```python
# src/finance_data/provider/fundamental/models.py
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class FinancialSummary:
    symbol: str
    period: str             # YYYYMMDD 报告期
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    roe: Optional[float] = None
    gross_margin: Optional[float] = None
    cash_flow: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "period": self.period,
                "revenue": self.revenue, "net_profit": self.net_profit,
                "roe": self.roe, "gross_margin": self.gross_margin,
                "cash_flow": self.cash_flow}


@dataclass
class DividendRecord:
    symbol: str
    ex_date: str
    per_share: float
    record_date: str

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "ex_date": self.ex_date,
                "per_share": self.per_share, "record_date": self.record_date}


@dataclass
class EarningsForecast:
    symbol: str
    period: str
    forecast_type: str      # 预增/预减/扭亏/首亏/续盈/续亏/略增/略减
    change_low: Optional[float] = None
    change_high: Optional[float] = None
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "period": self.period,
                "forecast_type": self.forecast_type,
                "change_low": self.change_low,
                "change_high": self.change_high,
                "summary": self.summary}
```

**Step 2: 写 akshare fundamental 测试**

```python
# tests/provider/fundamental/test_akshare.py
from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.fundamental.akshare import (
    get_financial_summary, get_dividend, get_earnings_forecast
)
from finance_data.provider.types import DataResult, DataFetchError

@pytest.fixture
def mock_financial_df():
    return pd.DataFrame([{
        "报告期": "20231231", "营业总收入": 1.8e11,
        "净利润": 4.6e10, "净资产收益率": 11.2,
        "毛利率": 28.5, "经营现金流量净额": 5.2e10,
    }])

def test_get_financial_summary_fields(mock_financial_df):
    with patch("finance_data.provider.fundamental.akshare.ak.stock_financial_abstract",
               return_value=mock_financial_df):
        result = get_financial_summary("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["roe"] == 11.2

@pytest.fixture
def mock_dividend_df():
    return pd.DataFrame([{
        "除权除息日": "20231215", "每股分红": 0.248, "股权登记日": "20231214",
    }])

def test_get_dividend_fields(mock_dividend_df):
    with patch("finance_data.provider.fundamental.akshare.ak.stock_fhps_detail_em",
               return_value=mock_dividend_df):
        result = get_dividend("000001")
    row = result.data[0]
    assert row["per_share"] == 0.248
```

**Step 3: 实现 fundamental/akshare.py**

```python
# src/finance_data/provider/fundamental/akshare.py
import contextlib, requests
import akshare as ak
from finance_data.provider.fundamental.models import (
    FinancialSummary, DividendRecord, EarningsForecast
)
from finance_data.provider.types import DataResult, DataFetchError

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


def _opt(val):
    try:
        v = float(val)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def get_financial_summary(symbol: str) -> DataResult:
    try:
        with _no_proxy():
            df = ak.stock_financial_abstract(symbol=symbol)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_financial_abstract", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_financial_abstract", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_financial_abstract", f"无数据: {symbol}", "data")

    rows = [FinancialSummary(
        symbol=symbol,
        period=str(r.get("报告期", "")).replace("-", ""),
        revenue=_opt(r.get("营业总收入")),
        net_profit=_opt(r.get("净利润")),
        roe=_opt(r.get("净资产收益率")),
        gross_margin=_opt(r.get("毛利率")),
        cash_flow=_opt(r.get("经营现金流量净额")),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "symbol": symbol})


def get_dividend(symbol: str) -> DataResult:
    try:
        with _no_proxy():
            df = ak.stock_fhps_detail_em(symbol=symbol)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_fhps_detail_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_fhps_detail_em", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_fhps_detail_em", f"无数据: {symbol}", "data")

    rows = [DividendRecord(
        symbol=symbol,
        ex_date=str(r.get("除权除息日", "")).replace("-", ""),
        per_share=float(r.get("每股分红", 0)),
        record_date=str(r.get("股权登记日", "")).replace("-", ""),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "symbol": symbol})


def get_earnings_forecast(symbol: str) -> DataResult:
    try:
        with _no_proxy():
            df = ak.stock_yjyg_em(symbol=symbol)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_yjyg_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_yjyg_em", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_yjyg_em", f"无数据: {symbol}", "data")

    rows = [EarningsForecast(
        symbol=symbol,
        period=str(r.get("报告期", "")).replace("-", ""),
        forecast_type=str(r.get("业绩变动类型", "")),
        change_low=_opt(r.get("业绩变动幅度-低")),
        change_high=_opt(r.get("业绩变动幅度-高")),
        summary=str(r.get("业绩变动原因", "")),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "symbol": symbol})
```

**Step 4: 实现 fundamental/tushare.py（使用 pro.income、pro.fina_indicator）**

```python
# src/finance_data/provider/fundamental/tushare.py
import os
import tushare as ts
from finance_data.provider.fundamental.models import FinancialSummary, DividendRecord
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _get_pro():
    token = os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        raise DataFetchError("tushare", "init", "TUSHARE_TOKEN 未设置", "auth")
    pro = ts.pro_api(token=token)
    api_url = os.environ.get("TUSHARE_API_URL", "")
    if api_url:
        pro._DataApi__token = token
        pro._DataApi__http_url = api_url
    return pro


def _ts_code(symbol: str) -> str:
    if "." in symbol:
        return symbol
    return f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"


def _opt(val):
    try:
        v = float(val)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def get_financial_summary(symbol: str) -> DataResult:
    pro = _get_pro()
    ts_code = _ts_code(symbol)
    try:
        df_income = pro.income(ts_code=ts_code, fields="end_date,total_revenue,n_income")
        df_fina = pro.fina_indicator(ts_code=ts_code,
                                     fields="end_date,roe,grossprofit_margin,n_cashflow_act")
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "income/fina_indicator", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "income/fina_indicator", reason, kind) from e

    if df_income is None or df_income.empty:
        raise DataFetchError("tushare", "income", f"无数据: {symbol}", "data")

    fina_map = {}
    if df_fina is not None and not df_fina.empty:
        for _, r in df_fina.iterrows():
            fina_map[str(r.get("end_date", ""))] = r

    rows = []
    for _, r in df_income.iterrows():
        period = str(r.get("end_date", ""))
        fi = fina_map.get(period, {})
        rows.append(FinancialSummary(
            symbol=symbol, period=period.replace("-", ""),
            revenue=_opt(r.get("total_revenue")),
            net_profit=_opt(r.get("n_income")),
            roe=_opt(fi.get("roe")) if fi else None,
            gross_margin=_opt(fi.get("grossprofit_margin")) if fi else None,
            cash_flow=_opt(fi.get("n_cashflow_act")) if fi else None,
        ).to_dict())

    return DataResult(data=rows, source="tushare", meta={"rows": len(rows), "symbol": symbol})


def get_dividend(symbol: str) -> DataResult:
    pro = _get_pro()
    ts_code = _ts_code(symbol)
    try:
        df = pro.dividend(ts_code=ts_code,
                          fields="ex_date,div_cash,record_date")
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "dividend", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "dividend", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "dividend", f"无数据: {symbol}", "data")

    rows = [DividendRecord(
        symbol=symbol,
        ex_date=str(r.get("ex_date", "")).replace("-", ""),
        per_share=float(r.get("div_cash", 0) or 0),
        record_date=str(r.get("record_date", "")).replace("-", ""),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="tushare", meta={"rows": len(rows), "symbol": symbol})


def get_earnings_forecast(symbol: str) -> DataResult:
    raise DataFetchError("tushare", "get_earnings_forecast",
                         "tushare 业绩预告需较高权限，降级使用 akshare", "auth")
```

**Step 5: 添加 MCP tools**

```python
from finance_data.provider.fundamental.akshare import (
    get_financial_summary as ak_fin_summary,
    get_dividend as ak_dividend,
    get_earnings_forecast as ak_earnings,
)
from finance_data.provider.fundamental.tushare import (
    get_financial_summary as ts_fin_summary,
    get_dividend as ts_dividend,
    get_earnings_forecast as ts_earnings,
)

@mcp.tool()
async def tool_get_financial_summary(symbol: str) -> str:
    """获取个股财务摘要（营收、净利润、ROE、毛利率）。"""
    for name, fn in [("akshare", ak_fin_summary), ("tushare", ts_fin_summary)]:
        try:
            return _to_json(fn(symbol))
        except Exception as e:
            logger.warning(f"{name} get_financial_summary 失败: {e}")
    return json.dumps({"error": "所有数据源均失败"}, ensure_ascii=False)

@mcp.tool()
async def tool_get_dividend(symbol: str) -> str:
    """获取个股历史分红记录。"""
    for name, fn in [("akshare", ak_dividend), ("tushare", ts_dividend)]:
        try:
            return _to_json(fn(symbol))
        except Exception as e:
            logger.warning(f"{name} get_dividend 失败: {e}")
    return json.dumps({"error": "所有数据源均失败"}, ensure_ascii=False)

@mcp.tool()
async def tool_get_earnings_forecast(symbol: str) -> str:
    """获取个股业绩预告。"""
    for name, fn in [("akshare", ak_earnings), ("tushare", ts_earnings)]:
        try:
            return _to_json(fn(symbol))
        except Exception as e:
            logger.warning(f"{name} get_earnings_forecast 失败: {e}")
    return json.dumps({"error": "所有数据源均失败"}, ensure_ascii=False)
```

**Step 6: 验证 & Commit**

```bash
.venv/bin/pytest tests/ -v
git add src/finance_data/provider/fundamental/ tests/provider/fundamental/ src/finance_data/mcp/server.py
git commit -m "feat(fundamental): 接入财务基本面接口 (akshare+tushare)"
```

---

## Task 8: cashflow 领域 — 资金流向

**Files:**
- Create: `src/finance_data/provider/cashflow/` (models, akshare, tushare, __init__)
- Create: `tests/provider/cashflow/`
- Modify: `src/finance_data/mcp/server.py`

**Step 1: 实现 cashflow/models.py**

```python
# src/finance_data/provider/cashflow/models.py
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class FundFlow:
    symbol: str
    date: str
    net_inflow: float       # 净流入（元）
    net_inflow_pct: float   # 净流入占比 %
    main_inflow: float      # 主力净流入
    main_inflow_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "date": self.date,
                "net_inflow": self.net_inflow,
                "net_inflow_pct": self.net_inflow_pct,
                "main_inflow": self.main_inflow,
                "main_inflow_pct": self.main_inflow_pct}
```

**Step 2: 写测试**

```python
# tests/provider/cashflow/test_akshare.py
from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.cashflow.akshare import get_fund_flow
from finance_data.provider.types import DataResult, DataFetchError

@pytest.fixture
def mock_flow_df():
    return pd.DataFrame([{
        "日期": "2024-01-02",
        "净流入": 1.2e8, "净流入占比": 2.3,
        "主力净流入": 8.5e7, "主力净流入占比": 1.6,
    }])

def test_get_fund_flow_returns_data_result(mock_flow_df):
    with patch("finance_data.provider.cashflow.akshare.ak.stock_individual_fund_flow",
               return_value=mock_flow_df):
        result = get_fund_flow("000001")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"

def test_get_fund_flow_fields(mock_flow_df):
    with patch("finance_data.provider.cashflow.akshare.ak.stock_individual_fund_flow",
               return_value=mock_flow_df):
        result = get_fund_flow("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["net_inflow"] == 1.2e8
```

**Step 3: 实现 cashflow/akshare.py**

```python
# src/finance_data/provider/cashflow/akshare.py
import contextlib, requests
import akshare as ak
from finance_data.provider.cashflow.models import FundFlow
from finance_data.provider.types import DataResult, DataFetchError

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


def get_fund_flow(symbol: str, market: str = "沪深A") -> DataResult:
    """获取个股资金流向（近期每日）。"""
    try:
        with _no_proxy():
            df = ak.stock_individual_fund_flow(stock=symbol, market=market)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_individual_fund_flow", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_individual_fund_flow", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_individual_fund_flow", f"无数据: {symbol}", "data")

    rows = [FundFlow(
        symbol=symbol,
        date=str(r.get("日期", "")).replace("-", ""),
        net_inflow=float(r.get("净流入", 0) or 0),
        net_inflow_pct=float(r.get("净流入占比", 0) or 0),
        main_inflow=float(r.get("主力净流入", 0) or 0),
        main_inflow_pct=float(r.get("主力净流入占比", 0) or 0),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="akshare", meta={"rows": len(rows), "symbol": symbol})
```

**Step 4: 实现 cashflow/tushare.py（tushare 无直接资金流向接口）**

```python
# src/finance_data/provider/cashflow/tushare.py
from finance_data.provider.types import DataResult, DataFetchError

def get_fund_flow(symbol: str, **kwargs) -> DataResult:
    raise DataFetchError("tushare", "get_fund_flow",
                         "tushare 无个股资金流向接口", "data")
```

**Step 5: 添加 MCP tool & 验证 & Commit**

```python
from finance_data.provider.cashflow.akshare import get_fund_flow as ak_fund_flow
from finance_data.provider.cashflow.tushare import get_fund_flow as ts_fund_flow

@mcp.tool()
async def tool_get_fund_flow(symbol: str) -> str:
    """获取个股资金流向（主力净流入等）。"""
    for name, fn in [("akshare", ak_fund_flow), ("tushare", ts_fund_flow)]:
        try:
            return _to_json(fn(symbol))
        except Exception as e:
            logger.warning(f"{name} get_fund_flow 失败: {e}")
    return json.dumps({"error": "所有数据源均失败"}, ensure_ascii=False)
```

```bash
.venv/bin/pytest tests/ -v
git add src/finance_data/provider/cashflow/ tests/provider/cashflow/ src/finance_data/mcp/server.py
git commit -m "feat(cashflow): 接入资金流向接口 (akshare)"
```

---

## Task 9: calendar 领域 — 交易日历（仅 tushare）

**Files:**
- Create: `src/finance_data/provider/calendar/` (models, tushare, __init__)
- Create: `tests/provider/calendar/`
- Modify: `src/finance_data/mcp/server.py`

**Step 1: 实现 calendar/models.py**

```python
# src/finance_data/provider/calendar/models.py
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class TradeDate:
    date: str       # YYYYMMDD
    is_open: bool

    def to_dict(self) -> Dict[str, Any]:
        return {"date": self.date, "is_open": self.is_open}
```

**Step 2: 写测试**

```python
# tests/provider/calendar/test_tushare.py
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from finance_data.provider.calendar.tushare import get_trade_calendar
from finance_data.provider.types import DataResult, DataFetchError

@pytest.fixture
def mock_pro():
    return MagicMock()

@pytest.fixture
def mock_cal_df():
    return pd.DataFrame([
        {"cal_date": "20240101", "is_open": 0},
        {"cal_date": "20240102", "is_open": 1},
    ])

def test_get_trade_calendar_returns_data_result(mock_pro, mock_cal_df):
    mock_pro.trade_cal.return_value = mock_cal_df
    with patch("finance_data.provider.calendar.tushare._get_pro", return_value=mock_pro):
        result = get_trade_calendar(start="20240101", end="20240102")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert len(result.data) == 2

def test_get_trade_calendar_fields(mock_pro, mock_cal_df):
    mock_pro.trade_cal.return_value = mock_cal_df
    with patch("finance_data.provider.calendar.tushare._get_pro", return_value=mock_pro):
        result = get_trade_calendar(start="20240101", end="20240102")
    assert result.data[0] == {"date": "20240101", "is_open": False}
    assert result.data[1] == {"date": "20240102", "is_open": True}
```

**Step 3: 实现 calendar/tushare.py**

```python
# src/finance_data/provider/calendar/tushare.py
import os
import tushare as ts
from finance_data.provider.calendar.models import TradeDate
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _get_pro():
    token = os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        raise DataFetchError("tushare", "init", "TUSHARE_TOKEN 未设置", "auth")
    pro = ts.pro_api(token=token)
    api_url = os.environ.get("TUSHARE_API_URL", "")
    if api_url:
        pro._DataApi__token = token
        pro._DataApi__http_url = api_url
    return pro


def get_trade_calendar(start: str, end: str, exchange: str = "SSE") -> DataResult:
    """获取交易日历。"""
    pro = _get_pro()
    try:
        df = pro.trade_cal(exchange=exchange, start_date=start, end_date=end,
                           fields="cal_date,is_open")
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "trade_cal", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "trade_cal", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "trade_cal", f"无数据: {start}-{end}", "data")

    rows = [TradeDate(
        date=str(r["cal_date"]),
        is_open=bool(int(r.get("is_open", 0))),
    ).to_dict() for _, r in df.iterrows()]

    return DataResult(data=rows, source="tushare",
                      meta={"rows": len(rows), "start": start, "end": end})
```

**Step 4: MCP tool & 验证 & Commit**

```python
from finance_data.provider.calendar.tushare import get_trade_calendar as ts_calendar

@mcp.tool()
async def tool_get_trade_calendar(start: str, end: str) -> str:
    """获取交易日历（is_open=true 为交易日）。start/end 格式 YYYYMMDD。"""
    try:
        return _to_json(ts_calendar(start=start, end=end))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
```

```bash
.venv/bin/pytest tests/ -v
git add src/finance_data/provider/calendar/ tests/provider/calendar/ src/finance_data/mcp/server.py
git commit -m "feat(calendar): 接入交易日历接口 (tushare)"
```

---

## Task 10: market 领域 — 市场统计

**Files:**
- Create: `src/finance_data/provider/market/` (models, akshare, tushare, __init__)
- Create: `tests/provider/market/`
- Modify: `src/finance_data/mcp/server.py`

**Step 1: 实现 market/models.py**

```python
# src/finance_data/provider/market/models.py
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class MarketStats:
    date: str
    total_count: int
    up_count: int
    down_count: int
    flat_count: int
    total_amount: Optional[float] = None    # 总成交额（元）

    def to_dict(self) -> Dict[str, Any]:
        return {"date": self.date, "total_count": self.total_count,
                "up_count": self.up_count, "down_count": self.down_count,
                "flat_count": self.flat_count, "total_amount": self.total_amount}
```

**Step 2: 写测试**

```python
# tests/provider/market/test_akshare.py
from unittest.mock import patch
import pandas as pd
import datetime
import pytest
from finance_data.provider.market.akshare import get_market_stats
from finance_data.provider.types import DataResult, DataFetchError

@pytest.fixture
def mock_spot_df():
    # 模拟 50 只股票的实时行情数据
    rows = []
    for i in range(30):
        rows.append({"代码": f"{i:06d}", "涨跌幅": 1.5, "成交额": 1e7})
    for i in range(30, 45):
        rows.append({"代码": f"{i:06d}", "涨跌幅": -0.8, "成交额": 8e6})
    for i in range(45, 50):
        rows.append({"代码": f"{i:06d}", "涨跌幅": 0.0, "成交额": 5e6})
    return pd.DataFrame(rows)

def test_get_market_stats_returns_data_result(mock_spot_df):
    with patch("finance_data.provider.market.akshare.ak.stock_zh_a_spot_em",
               return_value=mock_spot_df):
        result = get_market_stats()
    assert isinstance(result, DataResult)
    assert result.source == "akshare"

def test_get_market_stats_counts(mock_spot_df):
    with patch("finance_data.provider.market.akshare.ak.stock_zh_a_spot_em",
               return_value=mock_spot_df):
        result = get_market_stats()
    row = result.data[0]
    assert row["up_count"] == 30
    assert row["down_count"] == 15
    assert row["flat_count"] == 5
    assert row["total_count"] == 50
```

**Step 3: 实现 market/akshare.py**

```python
# src/finance_data/provider/market/akshare.py
import contextlib, datetime, requests
import akshare as ak
from finance_data.provider.market.models import MarketStats
from finance_data.provider.types import DataResult, DataFetchError

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


def get_market_stats() -> DataResult:
    """获取当日市场涨跌统计。"""
    try:
        with _no_proxy():
            df = ak.stock_zh_a_spot_em()
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "stock_zh_a_spot_em", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "stock_zh_a_spot_em", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "stock_zh_a_spot_em", "无数据", "data")

    pct = df["涨跌幅"].fillna(0)
    up = int((pct > 0).sum())
    down = int((pct < 0).sum())
    flat = int((pct == 0).sum())
    total_amount = float(df["成交额"].sum()) if "成交额" in df.columns else None

    stats = MarketStats(
        date=datetime.date.today().strftime("%Y%m%d"),
        total_count=len(df),
        up_count=up,
        down_count=down,
        flat_count=flat,
        total_amount=total_amount,
    )
    return DataResult(data=[stats.to_dict()], source="akshare", meta={"rows": 1})
```

**Step 4: 实现 market/tushare.py**

```python
# src/finance_data/provider/market/tushare.py
from finance_data.provider.types import DataResult, DataFetchError

def get_market_stats() -> DataResult:
    raise DataFetchError("tushare", "get_market_stats",
                         "tushare 无直接市场统计接口", "data")
```

**Step 5: MCP tool & 验证 & Commit**

```python
from finance_data.provider.market.akshare import get_market_stats as ak_market
from finance_data.provider.market.tushare import get_market_stats as ts_market

@mcp.tool()
async def tool_get_market_stats() -> str:
    """获取当日市场涨跌家数、总成交额等统计信息。"""
    for name, fn in [("akshare", ak_market), ("tushare", ts_market)]:
        try:
            return _to_json(fn())
        except Exception as e:
            logger.warning(f"{name} get_market_stats 失败: {e}")
    return json.dumps({"error": "所有数据源均失败"}, ensure_ascii=False)
```

```bash
.venv/bin/pytest tests/ -v
git add src/finance_data/provider/market/ tests/provider/market/ src/finance_data/mcp/server.py
git commit -m "feat(market): 接入市场统计接口"
```

---

## 完成验证

全部 10 个领域实现后执行：

```bash
# 完整测试
.venv/bin/pytest tests/ -v --tb=short

# 确认 MCP tools 数量
grep "@mcp.tool" src/finance_data/mcp/server.py | wc -l
# 预期：14 个 tools
# tool_get_stock_info, tool_get_kline, tool_get_realtime_quote,
# tool_get_index_quote, tool_get_index_history, tool_get_sector_rank,
# tool_get_chip_distribution, tool_get_financial_summary,
# tool_get_dividend, tool_get_earnings_forecast, tool_get_fund_flow,
# tool_get_trade_calendar, tool_get_market_stats

# 更新 CLAUDE.md 接口列表
```

**最终 commit:**
```bash
git add CLAUDE.md
git commit -m "docs: 更新 CLAUDE.md 接口列表（全量 10 领域接入完成）"
```
