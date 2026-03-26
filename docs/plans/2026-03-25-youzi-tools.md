# 游资交易补充工具 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 新增 3 个游资交易场景工具：历史资金流、概念板块排名、概念板块成分股。

**Architecture:** 沿用 domain-first 四层架构（interface → provider → service → mcp），每个工具遵循 Protocol + dataclass + Dispatcher 模式。仅接入 akshare provider（无需 token）。

**Tech Stack:** Python 3.11, akshare, pydantic, fastmcp, pytest

---

## Task 1: 历史资金流 — Interface 层

**Files:**
- Create: `src/finance_data/interface/cashflow/history.py`
- Create: `tests/provider/cashflow/__init__.py`（已存在则跳过）

**Step 1: 创建 interface 定义**

```python
# src/finance_data/interface/cashflow/history.py
"""个股历史资金流向接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class CapitalFlowHistoryProtocol(Protocol):
    def get_capital_flow_history(self, symbol: str) -> DataResult: ...


@dataclass
class CapitalFlowDay:
    symbol: str
    date: str
    close: float
    pct_chg: float
    main_net_inflow: float
    main_net_inflow_pct: float
    super_large_net_inflow: float
    super_large_net_inflow_pct: float
    large_net_inflow: float
    large_net_inflow_pct: float
    medium_net_inflow: float
    medium_net_inflow_pct: float
    small_net_inflow: float
    small_net_inflow_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "date": self.date,
            "close": self.close,
            "pct_chg": self.pct_chg,
            "main_net_inflow": self.main_net_inflow,
            "main_net_inflow_pct": self.main_net_inflow_pct,
            "super_large_net_inflow": self.super_large_net_inflow,
            "super_large_net_inflow_pct": self.super_large_net_inflow_pct,
            "large_net_inflow": self.large_net_inflow,
            "large_net_inflow_pct": self.large_net_inflow_pct,
            "medium_net_inflow": self.medium_net_inflow,
            "medium_net_inflow_pct": self.medium_net_inflow_pct,
            "small_net_inflow": self.small_net_inflow,
            "small_net_inflow_pct": self.small_net_inflow_pct,
        }
```

**Step 2: Commit**

```bash
git add src/finance_data/interface/cashflow/history.py
git commit -m "feat(interface): 历史资金流 Protocol + dataclass"
```

---

## Task 2: 历史资金流 — Provider 层

**Files:**
- Create: `src/finance_data/provider/akshare/cashflow/history.py`
- Create: `tests/provider/cashflow/test_capital_flow_history.py`

**Step 1: 写测试**

```python
# tests/provider/cashflow/test_capital_flow_history.py
"""历史资金流 akshare provider 测试"""
from unittest.mock import patch

import pandas as pd
import pytest

from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.cashflow.history import AkshareCapitalFlowHistory


@pytest.fixture
def mock_fund_flow_df():
    return pd.DataFrame([
        {
            "日期": "2026-03-25",
            "收盘价": 1410.27,
            "涨跌幅": 0.21,
            "主力净流入-净额": 1.5e8,
            "主力净流入-净占比": 4.08,
            "超大单净流入-净额": 8.0e7,
            "超大单净流入-净占比": 2.17,
            "大单净流入-净额": 7.0e7,
            "大单净流入-净占比": 1.90,
            "中单净流入-净额": -6.0e7,
            "中单净流入-净占比": -1.63,
            "小单净流入-净额": -9.0e7,
            "小单净流入-净占比": -2.45,
        },
    ])


_PATCH_TARGET = "finance_data.provider.akshare.cashflow.history.ak.stock_individual_fund_flow"


class TestAkshareCapitalFlowHistory:
    def test_returns_data_result(self, mock_fund_flow_df):
        with patch(_PATCH_TARGET, return_value=mock_fund_flow_df):
            result = AkshareCapitalFlowHistory().get_capital_flow_history("600519")
        assert isinstance(result, DataResult)
        assert result.source == "akshare"
        assert len(result.data) == 1

    def test_fields_mapped(self, mock_fund_flow_df):
        with patch(_PATCH_TARGET, return_value=mock_fund_flow_df):
            result = AkshareCapitalFlowHistory().get_capital_flow_history("600519")
        row = result.data[0]
        assert row["symbol"] == "600519"
        assert row["date"] == "20260325"
        assert row["close"] == 1410.27
        assert row["main_net_inflow"] == 1.5e8
        assert row["main_net_inflow_pct"] == 4.08
        assert row["super_large_net_inflow"] == 8.0e7
        assert row["large_net_inflow"] == 7.0e7
        assert row["medium_net_inflow"] == -6.0e7
        assert row["small_net_inflow"] == -9.0e7

    def test_sh_market_detection(self, mock_fund_flow_df):
        with patch(_PATCH_TARGET, return_value=mock_fund_flow_df) as mock_fn:
            AkshareCapitalFlowHistory().get_capital_flow_history("600519")
        mock_fn.assert_called_once_with(stock="600519", market="sh")

    def test_sz_market_detection(self, mock_fund_flow_df):
        with patch(_PATCH_TARGET, return_value=mock_fund_flow_df) as mock_fn:
            AkshareCapitalFlowHistory().get_capital_flow_history("000001")
        mock_fn.assert_called_once_with(stock="000001", market="sz")

    def test_network_error(self):
        with patch(_PATCH_TARGET, side_effect=ConnectionError("timeout")):
            with pytest.raises(DataFetchError) as exc:
                AkshareCapitalFlowHistory().get_capital_flow_history("600519")
        assert exc.value.kind == "network"

    def test_empty_raises(self):
        with patch(_PATCH_TARGET, return_value=pd.DataFrame()):
            with pytest.raises(DataFetchError) as exc:
                AkshareCapitalFlowHistory().get_capital_flow_history("600519")
        assert exc.value.kind == "data"
```

**Step 2: 运行测试，确认失败**

Run: `.venv/bin/pytest tests/provider/cashflow/test_capital_flow_history.py -v`
Expected: FAIL (模块不存在)

**Step 3: 实现 provider**

```python
# src/finance_data/provider/akshare/cashflow/history.py
"""个股历史资金流向 - akshare 实现"""
import contextlib

import akshare as ak
import requests

from finance_data.interface.cashflow.history import CapitalFlowDay
from finance_data.interface.types import DataFetchError, DataResult

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


class AkshareCapitalFlowHistory:
    def get_capital_flow_history(self, symbol: str) -> DataResult:
        market = "sh" if symbol.startswith("6") else "sz"
        try:
            with _no_proxy():
                df = ak.stock_individual_fund_flow(stock=symbol, market=market)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_individual_fund_flow", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_individual_fund_flow", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_individual_fund_flow",
                                 f"无数据: {symbol}", "data")

        rows = [CapitalFlowDay(
            symbol=symbol,
            date=str(r.get("日期", "")).replace("-", ""),
            close=float(r.get("收盘价", 0) or 0),
            pct_chg=float(r.get("涨跌幅", 0) or 0),
            main_net_inflow=float(r.get("主力净流入-净额", 0) or 0),
            main_net_inflow_pct=float(r.get("主力净流入-净占比", 0) or 0),
            super_large_net_inflow=float(r.get("超大单净流入-净额", 0) or 0),
            super_large_net_inflow_pct=float(r.get("超大单净流入-净占比", 0) or 0),
            large_net_inflow=float(r.get("大单净流入-净额", 0) or 0),
            large_net_inflow_pct=float(r.get("大单净流入-净占比", 0) or 0),
            medium_net_inflow=float(r.get("中单净流入-净额", 0) or 0),
            medium_net_inflow_pct=float(r.get("中单净流入-净占比", 0) or 0),
            small_net_inflow=float(r.get("小单净流入-净额", 0) or 0),
            small_net_inflow_pct=float(r.get("小单净流入-净占比", 0) or 0),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "symbol": symbol})
```

**Step 4: 运行测试，确认通过**

Run: `.venv/bin/pytest tests/provider/cashflow/test_capital_flow_history.py -v`
Expected: 6 passed

**Step 5: Commit**

```bash
git add src/finance_data/provider/akshare/cashflow/history.py tests/provider/cashflow/test_capital_flow_history.py
git commit -m "feat(provider): 历史资金流 akshare 实现 + 测试"
```

---

## Task 3: 历史资金流 — Service + MCP + Registry

**Files:**
- Modify: `src/finance_data/service/cashflow.py` — 新增 dispatcher
- Modify: `src/finance_data/mcp/server.py` — 新增 tool
- Modify: `src/finance_data/provider/metadata/registry.py` — 新增 ToolMeta

**Step 1: 扩展 service 层**

在 `src/finance_data/service/cashflow.py` 末尾追加：

```python
from finance_data.interface.cashflow.history import CapitalFlowHistoryProtocol
from finance_data.provider.akshare.cashflow.history import AkshareCapitalFlowHistory


class _CapitalFlowHistoryDispatcher:
    def __init__(self, providers: list[CapitalFlowHistoryProtocol]):
        self._providers = providers

    def get_capital_flow_history(self, symbol: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_capital_flow_history(symbol)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_capital_flow_history", "所有数据源均失败", "data")


capital_flow_history = _CapitalFlowHistoryDispatcher(providers=[AkshareCapitalFlowHistory()])
```

**Step 2: 添加 MCP tool**

在 `src/finance_data/mcp/server.py` 顶部 import 区追加：

```python
from finance_data.service.cashflow import stock_capital_flow, capital_flow_history
```

（替换原来的 `from finance_data.service.cashflow import stock_capital_flow`）

在文件末尾追加：

```python
@mcp.tool()
async def tool_get_capital_flow_history(
    symbol: str,
) -> str:
    """
    获取个股历史资金流向（近 120 个交易日），含主力/超大单/大单/中单/小单净流入。

    数据源: 仅 akshare（东方财富）
    实时性: 收盘后更新(T+1_16:00)
    历史查询: 返回近 120 交易日

    Args:
        symbol: 股票代码，如 "600519"

    Returns:
        JSON 列表，每条包含 date、close、pct_chg、
        main_net_inflow(主力净流入元)、main_net_inflow_pct(%)、
        super_large_net_inflow(超大单元)、large_net_inflow(大单元)、
        medium_net_inflow(中单元)、small_net_inflow(小单元)及对应百分比
    """
    try:
        return _to_json(capital_flow_history.get_capital_flow_history(symbol=symbol))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
```

**Step 3: 注册 ToolMeta**

在 `src/finance_data/provider/metadata/registry.py` 的 `TOOL_REGISTRY` dict 末尾（`}` 之前）追加：

```python
    "tool_get_capital_flow_history": ToolMeta(
        name="tool_get_capital_flow_history",
        description="获取个股历史资金流向（近120交易日，主力/超大单/大单/中单/小单）",
        domain="cashflow",
        entity="stock",
        scope="daily",
        data_freshness=DataFreshness.END_OF_DAY,
        update_timing=UpdateTiming.T_PLUS_1_16_00,
        supports_history=True,
        history_start="近120交易日",
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_individual_fund_flow",
        limitations=["仅返回近120交易日；金额单位为元（非万元）"],
        return_fields=["date", "close", "pct_chg", "main_net_inflow", "main_net_inflow_pct",
                        "super_large_net_inflow", "large_net_inflow", "medium_net_inflow",
                        "small_net_inflow"],
    ),
```

**Step 4: 运行全量测试**

Run: `.venv/bin/pytest tests/ -v --tb=short`
Expected: 所有测试通过

**Step 5: 运行 metadata 校验**

Run: `.venv/bin/python -c "from finance_data.provider.metadata.validator import run_validation_report; print(run_validation_report())"`
Expected: 无新增错误

**Step 6: Commit**

```bash
git add src/finance_data/service/cashflow.py src/finance_data/mcp/server.py src/finance_data/provider/metadata/registry.py
git commit -m "feat: 历史资金流 service + MCP tool + registry"
```

---

## Task 4: 概念板块排名 — Interface 层

**Files:**
- Create: `src/finance_data/interface/concept/__init__.py`
- Create: `src/finance_data/interface/concept/rank.py`

**Step 1: 创建目录和 interface**

```python
# src/finance_data/interface/concept/__init__.py
```

```python
# src/finance_data/interface/concept/rank.py
"""概念板块排名接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from finance_data.interface.types import DataResult


class ConceptBoardRankProtocol(Protocol):
    def get_concept_board_rank(self) -> DataResult: ...


@dataclass
class ConceptBoard:
    rank: int
    name: str
    code: str
    pct_chg: float
    total_mv: float
    turnover_rate: float
    up_count: Optional[int]
    down_count: Optional[int]
    leader_stock: str
    leader_pct_chg: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "name": self.name,
            "code": self.code,
            "pct_chg": self.pct_chg,
            "total_mv": self.total_mv,
            "turnover_rate": self.turnover_rate,
            "up_count": self.up_count,
            "down_count": self.down_count,
            "leader_stock": self.leader_stock,
            "leader_pct_chg": self.leader_pct_chg,
        }
```

**Step 2: Commit**

```bash
git add src/finance_data/interface/concept/
git commit -m "feat(interface): 概念板块排名 Protocol + dataclass"
```

---

## Task 5: 概念板块排名 — Provider 层

**Files:**
- Create: `src/finance_data/provider/akshare/concept/__init__.py`
- Create: `src/finance_data/provider/akshare/concept/rank.py`
- Create: `tests/provider/concept/__init__.py`
- Create: `tests/provider/concept/test_rank.py`

**Step 1: 写测试**

```python
# tests/provider/concept/test_rank.py
"""概念板块排名 akshare provider 测试"""
from unittest.mock import patch

import pandas as pd
import pytest

from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.concept.rank import AkshareConceptBoardRank


@pytest.fixture
def mock_concept_df():
    return pd.DataFrame([
        {
            "排名": 1,
            "板块名称": "人工智能",
            "板块代码": "BK0800",
            "最新价": 1234.56,
            "涨跌额": 23.45,
            "涨跌幅": 1.93,
            "总市值": 5.0e12,
            "换手率": 2.15,
            "上涨家数": 80,
            "下跌家数": 20,
            "领涨股票": "科大讯飞",
            "领涨股票-涨跌幅": 9.98,
        },
        {
            "排名": 2,
            "板块名称": "算力",
            "板块代码": "BK1077",
            "最新价": 987.65,
            "涨跌额": 15.32,
            "涨跌幅": 1.58,
            "总市值": 3.0e12,
            "换手率": 1.88,
            "上涨家数": 60,
            "下跌家数": 15,
            "领涨股票": "中科曙光",
            "领涨股票-涨跌幅": 7.55,
        },
    ])


_PATCH_TARGET = "finance_data.provider.akshare.concept.rank.ak.stock_board_concept_name_em"


class TestAkshareConceptBoardRank:
    def test_returns_data_result(self, mock_concept_df):
        with patch(_PATCH_TARGET, return_value=mock_concept_df):
            result = AkshareConceptBoardRank().get_concept_board_rank()
        assert isinstance(result, DataResult)
        assert result.source == "akshare"
        assert len(result.data) == 2

    def test_fields_mapped(self, mock_concept_df):
        with patch(_PATCH_TARGET, return_value=mock_concept_df):
            result = AkshareConceptBoardRank().get_concept_board_rank()
        row = result.data[0]
        assert row["rank"] == 1
        assert row["name"] == "人工智能"
        assert row["code"] == "BK0800"
        assert row["pct_chg"] == 1.93
        assert row["total_mv"] == 5.0e12
        assert row["turnover_rate"] == 2.15
        assert row["up_count"] == 80
        assert row["down_count"] == 20
        assert row["leader_stock"] == "科大讯飞"
        assert row["leader_pct_chg"] == 9.98

    def test_network_error(self):
        with patch(_PATCH_TARGET, side_effect=ConnectionError("timeout")):
            with pytest.raises(DataFetchError) as exc:
                AkshareConceptBoardRank().get_concept_board_rank()
        assert exc.value.kind == "network"

    def test_empty_raises(self):
        with patch(_PATCH_TARGET, return_value=pd.DataFrame()):
            with pytest.raises(DataFetchError) as exc:
                AkshareConceptBoardRank().get_concept_board_rank()
        assert exc.value.kind == "data"
```

**Step 2: 运行测试，确认失败**

Run: `.venv/bin/pytest tests/provider/concept/test_rank.py -v`
Expected: FAIL

**Step 3: 实现 provider**

```python
# src/finance_data/provider/akshare/concept/__init__.py
```

```python
# src/finance_data/provider/akshare/concept/rank.py
"""概念板块排名 - akshare 实现"""
import contextlib

import akshare as ak
import requests

from finance_data.interface.concept.rank import ConceptBoard
from finance_data.interface.types import DataFetchError, DataResult

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


class AkshareConceptBoardRank:
    def get_concept_board_rank(self) -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_board_concept_name_em()
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_board_concept_name_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_board_concept_name_em", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_board_concept_name_em", "无数据", "data")

        rows = [ConceptBoard(
            rank=int(r.get("排名", 0)),
            name=str(r.get("板块名称", "")),
            code=str(r.get("板块代码", "")),
            pct_chg=float(r.get("涨跌幅", 0) or 0),
            total_mv=float(r.get("总市值", 0) or 0),
            turnover_rate=float(r.get("换手率", 0) or 0),
            up_count=_opt_int(r.get("上涨家数")),
            down_count=_opt_int(r.get("下跌家数")),
            leader_stock=str(r.get("领涨股票", "")),
            leader_pct_chg=float(r.get("领涨股票-涨跌幅", 0) or 0),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare", meta={"rows": len(rows)})
```

**Step 4: 运行测试，确认通过**

Run: `.venv/bin/pytest tests/provider/concept/test_rank.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add src/finance_data/provider/akshare/concept/ src/finance_data/interface/concept/ tests/provider/concept/
git commit -m "feat(provider): 概念板块排名 akshare 实现 + 测试"
```

---

## Task 6: 概念板块成分股 — Interface 层

**Files:**
- Create: `src/finance_data/interface/concept/cons.py`

**Step 1: 创建 interface**

```python
# src/finance_data/interface/concept/cons.py
"""概念板块成分股接口定义"""
from dataclasses import dataclass
from typing import Any, Dict, Protocol

from finance_data.interface.types import DataResult


class ConceptBoardConsProtocol(Protocol):
    def get_concept_board_cons(self, symbol: str) -> DataResult: ...


@dataclass
class ConceptStock:
    symbol: str
    name: str
    price: float
    pct_chg: float
    volume: float
    amount: float
    amplitude: float
    turnover_rate: float
    pe: float
    pb: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "price": self.price,
            "pct_chg": self.pct_chg,
            "volume": self.volume,
            "amount": self.amount,
            "amplitude": self.amplitude,
            "turnover_rate": self.turnover_rate,
            "pe": self.pe,
            "pb": self.pb,
        }
```

**Step 2: Commit**

```bash
git add src/finance_data/interface/concept/cons.py
git commit -m "feat(interface): 概念板块成分股 Protocol + dataclass"
```

---

## Task 7: 概念板块成分股 — Provider 层

**Files:**
- Create: `src/finance_data/provider/akshare/concept/cons.py`
- Create: `tests/provider/concept/test_cons.py`

**Step 1: 写测试**

```python
# tests/provider/concept/test_cons.py
"""概念板块成分股 akshare provider 测试"""
from unittest.mock import patch

import pandas as pd
import pytest

from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.concept.cons import AkshareConceptBoardCons


@pytest.fixture
def mock_cons_df():
    return pd.DataFrame([
        {
            "序号": 1,
            "代码": "002230",
            "名称": "科大讯飞",
            "最新价": 55.88,
            "涨跌幅": 5.32,
            "涨跌额": 2.82,
            "成交量": 500000,
            "成交额": 2.8e9,
            "振幅": 6.15,
            "最高": 56.20,
            "最低": 53.10,
            "今开": 53.50,
            "昨收": 53.06,
            "换手率": 2.27,
            "市盈率-动态": 180.5,
            "市净率": 5.62,
        },
        {
            "序号": 2,
            "代码": "603019",
            "名称": "中科曙光",
            "最新价": 48.90,
            "涨跌幅": 3.18,
            "涨跌额": 1.50,
            "成交量": 300000,
            "成交额": 1.5e9,
            "振幅": 4.22,
            "最高": 49.30,
            "最低": 47.30,
            "今开": 47.50,
            "昨收": 47.40,
            "换手率": 1.55,
            "市盈率-动态": 42.3,
            "市净率": 3.88,
        },
    ])


_PATCH_TARGET = "finance_data.provider.akshare.concept.cons.ak.stock_board_concept_cons_em"


class TestAkshareConceptBoardCons:
    def test_returns_data_result(self, mock_cons_df):
        with patch(_PATCH_TARGET, return_value=mock_cons_df):
            result = AkshareConceptBoardCons().get_concept_board_cons("人工智能")
        assert isinstance(result, DataResult)
        assert result.source == "akshare"
        assert len(result.data) == 2

    def test_fields_mapped(self, mock_cons_df):
        with patch(_PATCH_TARGET, return_value=mock_cons_df):
            result = AkshareConceptBoardCons().get_concept_board_cons("人工智能")
        row = result.data[0]
        assert row["symbol"] == "002230"
        assert row["name"] == "科大讯飞"
        assert row["price"] == 55.88
        assert row["pct_chg"] == 5.32
        assert row["volume"] == 500000
        assert row["amount"] == 2.8e9
        assert row["amplitude"] == 6.15
        assert row["turnover_rate"] == 2.27
        assert row["pe"] == 180.5
        assert row["pb"] == 5.62

    def test_symbol_passed_through(self, mock_cons_df):
        with patch(_PATCH_TARGET, return_value=mock_cons_df) as mock_fn:
            AkshareConceptBoardCons().get_concept_board_cons("BK0800")
        mock_fn.assert_called_once_with(symbol="BK0800")

    def test_network_error(self):
        with patch(_PATCH_TARGET, side_effect=ConnectionError("timeout")):
            with pytest.raises(DataFetchError) as exc:
                AkshareConceptBoardCons().get_concept_board_cons("人工智能")
        assert exc.value.kind == "network"

    def test_empty_raises(self):
        with patch(_PATCH_TARGET, return_value=pd.DataFrame()):
            with pytest.raises(DataFetchError) as exc:
                AkshareConceptBoardCons().get_concept_board_cons("不存在板块")
        assert exc.value.kind == "data"
```

**Step 2: 运行测试，确认失败**

Run: `.venv/bin/pytest tests/provider/concept/test_cons.py -v`
Expected: FAIL

**Step 3: 实现 provider**

```python
# src/finance_data/provider/akshare/concept/cons.py
"""概念板块成分股 - akshare 实现"""
import contextlib

import akshare as ak
import requests

from finance_data.interface.concept.cons import ConceptStock
from finance_data.interface.types import DataFetchError, DataResult

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


class AkshareConceptBoardCons:
    def get_concept_board_cons(self, symbol: str) -> DataResult:
        try:
            with _no_proxy():
                df = ak.stock_board_concept_cons_em(symbol=symbol)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_board_concept_cons_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_board_concept_cons_em", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_board_concept_cons_em",
                                 f"无数据: {symbol}", "data")

        rows = [ConceptStock(
            symbol=str(r.get("代码", "")),
            name=str(r.get("名称", "")),
            price=float(r.get("最新价", 0) or 0),
            pct_chg=float(r.get("涨跌幅", 0) or 0),
            volume=float(r.get("成交量", 0) or 0),
            amount=float(r.get("成交额", 0) or 0),
            amplitude=float(r.get("振幅", 0) or 0),
            turnover_rate=float(r.get("换手率", 0) or 0),
            pe=float(r.get("市盈率-动态", 0) or 0),
            pb=float(r.get("市净率", 0) or 0),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "symbol": symbol})
```

**Step 4: 运行测试，确认通过**

Run: `.venv/bin/pytest tests/provider/concept/test_cons.py -v`
Expected: 5 passed

**Step 5: Commit**

```bash
git add src/finance_data/provider/akshare/concept/cons.py tests/provider/concept/test_cons.py
git commit -m "feat(provider): 概念板块成分股 akshare 实现 + 测试"
```

---

## Task 8: 概念板块 — Service + MCP + Registry

**Files:**
- Create: `src/finance_data/service/concept.py`
- Modify: `src/finance_data/mcp/server.py`
- Modify: `src/finance_data/provider/metadata/registry.py`

**Step 1: 创建 service**

```python
# src/finance_data/service/concept.py
"""概念板块 service - 统一对外入口"""
import logging

from finance_data.interface.concept.rank import ConceptBoardRankProtocol
from finance_data.interface.concept.cons import ConceptBoardConsProtocol
from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.akshare.concept.rank import AkshareConceptBoardRank
from finance_data.provider.akshare.concept.cons import AkshareConceptBoardCons

logger = logging.getLogger(__name__)


class _ConceptBoardRankDispatcher:
    def __init__(self, providers: list[ConceptBoardRankProtocol]):
        self._providers = providers

    def get_concept_board_rank(self) -> DataResult:
        for p in self._providers:
            try:
                return p.get_concept_board_rank()
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_concept_board_rank", "所有数据源均失败", "data")


class _ConceptBoardConsDispatcher:
    def __init__(self, providers: list[ConceptBoardConsProtocol]):
        self._providers = providers

    def get_concept_board_cons(self, symbol: str) -> DataResult:
        for p in self._providers:
            try:
                return p.get_concept_board_cons(symbol)
            except DataFetchError as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_concept_board_cons", "所有数据源均失败", "data")


concept_board_rank = _ConceptBoardRankDispatcher(providers=[AkshareConceptBoardRank()])
concept_board_cons = _ConceptBoardConsDispatcher(providers=[AkshareConceptBoardCons()])
```

**Step 2: 添加 MCP tools**

在 `src/finance_data/mcp/server.py` 顶部 import 区追加：

```python
from finance_data.service.concept import concept_board_rank, concept_board_cons
```

在文件末尾追加两个 tool：

```python
@mcp.tool()
async def tool_get_concept_board_rank() -> str:
    """
    获取概念板块涨跌排名（题材追踪核心工具）。

    数据源: 仅 akshare（东方财富概念板块）
    实时性: 盘中实时(T+0)
    历史查询: 不支持

    Returns:
        JSON 列表，每条包含 rank、name(板块名)、code(板块代码如BK0800)、
        pct_chg(涨跌幅%)、total_mv(总市值元)、turnover_rate(换手率%)、
        up_count(上涨家数)、down_count(下跌家数)、
        leader_stock(领涨股票名)、leader_pct_chg(领涨股涨跌幅%)
    """
    try:
        return _to_json(concept_board_rank.get_concept_board_rank())
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
async def tool_get_concept_board_cons(
    symbol: str,
) -> str:
    """
    获取概念板块成分股列表（题材扩散选股）。

    数据源: 仅 akshare（东方财富概念板块）
    实时性: 盘中实时(T+0)
    历史查询: 不支持

    Args:
        symbol: 板块名称（如"人工智能"）或板块代码（如"BK0800"）

    Returns:
        JSON 列表，每条包含 symbol(股票代码)、name(股票名)、
        price(最新价)、pct_chg(涨跌幅%)、volume(成交量)、amount(成交额元)、
        amplitude(振幅%)、turnover_rate(换手率%)、pe(动态市盈率)、pb(市净率)
    """
    try:
        return _to_json(concept_board_cons.get_concept_board_cons(symbol=symbol))
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
```

**Step 3: 注册 ToolMeta（2 条）**

在 `src/finance_data/provider/metadata/registry.py` 的 `TOOL_REGISTRY` dict 末尾追加：

```python
    "tool_get_concept_board_rank": ToolMeta(
        name="tool_get_concept_board_rank",
        description="获取概念板块涨跌排名（题材追踪）",
        domain="concept",
        entity="sector",
        scope="realtime",
        data_freshness=DataFreshness.REALTIME,
        update_timing=UpdateTiming.T_PLUS_0,
        supports_history=False,
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_board_concept_name_em",
        limitations=["仅 akshare，东方财富概念板块分类"],
        return_fields=["rank", "name", "code", "pct_chg", "total_mv", "turnover_rate",
                        "up_count", "down_count", "leader_stock", "leader_pct_chg"],
    ),

    "tool_get_concept_board_cons": ToolMeta(
        name="tool_get_concept_board_cons",
        description="获取概念板块成分股列表（题材扩散选股）",
        domain="concept",
        entity="stock",
        scope="realtime",
        data_freshness=DataFreshness.REALTIME,
        update_timing=UpdateTiming.T_PLUS_0,
        supports_history=False,
        source=DataSource.AKSHARE,
        source_priority="akshare",
        api_name="stock_board_concept_cons_em",
        limitations=["仅 akshare，东方财富概念板块分类"],
        return_fields=["symbol", "name", "price", "pct_chg", "volume", "amount",
                        "amplitude", "turnover_rate", "pe", "pb"],
    ),
```

**Step 4: 运行全量测试**

Run: `.venv/bin/pytest tests/ -v --tb=short`
Expected: 所有测试通过

**Step 5: 运行 metadata 校验**

Run: `.venv/bin/python -c "from finance_data.provider.metadata.validator import run_validation_report; print(run_validation_report())"`
Expected: 无新增错误

**Step 6: Commit**

```bash
git add src/finance_data/service/concept.py src/finance_data/mcp/server.py src/finance_data/provider/metadata/registry.py
git commit -m "feat: 概念板块排名+成分股 service + MCP tools + registry"
```

---

## Task 9: 更新 CLAUDE.md 接口列表

**Files:**
- Modify: `CLAUDE.md`

**Step 1: 更新接口数量和表格**

将 `## 当前接口（27 个）` 改为 `## 当前接口（30 个）`，在表格末尾追加：

```markdown
| `tool_get_capital_flow_history` | cashflow | 个股历史资金流向（近120日，5级分类），仅 akshare |
| `tool_get_concept_board_rank` | concept | 概念板块涨跌排名（题材追踪），仅 akshare |
| `tool_get_concept_board_cons` | concept | 概念板块成分股（题材扩散选股），仅 akshare |
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: 更新接口列表至 30 个"
```

---

## Task 10: 最终验证

**Step 1: 全量测试**

Run: `.venv/bin/pytest tests/ -v --tb=short`
Expected: 全部通过（含新增 15 个测试）

**Step 2: metadata 校验**

Run: `.venv/bin/python -c "from finance_data.provider.metadata.validator import run_validation_report; print(run_validation_report())"`

**Step 3: Push**

```bash
git push
```
