# Skill: 新增 FinanceData 接口

## 触发条件

当需要为 FinanceData 新增一个数据接口时使用此 Skill。

## 输入参数

- `domain`: 数据领域（如 stock, index, sector, market, flow, financial, lhb, margin）
- `interface_name`: 接口英文名称（如 `get_stock_capital_flow`）
- `description`: 一句话功能描述
- `data_source`: 数据源选择（akshare / tushare / both）
- `priority`: 优先使用的数据源（akshare 优先于 tushare）

## 执行步骤

### Step 1: 确定接口规范

根据接口特性确定以下元数据：

```
name:           tool_get_xxx
domain:          stock/index/sector/market/flow/financial/lhb/margin
entity:          实体类型
scope:           daily/historical/realtime
data_freshness: realtime | end_of_day | historical | quarterly
update_timing:  T+0 | T+1_15:30 | T+1_17:00 | next_trade_day_9:30 | quarterly
supports_history: true | false
history_start:   历史数据最早日期（如 "20180101"）
cache_ttl:      缓存TTL分钟数，0=无缓存
source:          akshare | tushare | both
source_priority: akshare | tushare
api_name:        实际API名称
limitations:     已知限制列表
```

### Step 2: 验证数据源能力

在接入前，必须确认数据源是否满足需求：

```bash
# 测试 akshare 接口
.venv/bin/python3 -c "
import akshare as ak
# 查看接口签名
help(ak.接口名)
# 测试返回字段
df = ak.接口名(参数)
print(df.columns.tolist())
print(df.head(2))
"

# 测试 tushare 接口（如需要）
.venv/bin/python3 -c "
from finance_data.provider.tushare.client import get_pro
pro = get_pro()
df = pro.接口名(参数)
print(df.columns.tolist())
"
```

### Step 3: 创建 Domain 目录结构

每个接口属于一个 domain，目录结构：

```
src/finance_data/provider/{domain}/
├── __init__.py           # 导出 get_xxx 函数
├── models.py              # 数据模型（dataclass）
├── akshare.py             # akshare provider
└── tushare.py            # tushare provider（可选）

tests/provider/{domain}/
├── __init__.py
├── test_akshare.py       # akshare 测试
└── test_tushare.py       # tushare 测试（可选）
```

### Step 4: 实现 Provider

#### 4.1 定义数据模型

```python
# src/finance_data/provider/{domain}/models.py
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class DomainData:
    date: str
    # ... 其他字段

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            # ...
        }
```

#### 4.2 实现 Akshare Provider

```python
# src/finance_data/provider/{domain}/akshare.py
"""{领域描述} - akshare"""
import contextlib
import requests
import akshare as ak

from finance_data.provider.{domain}.models import DomainData
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)

@contextlib.contextmanager
def _no_proxy():
    """禁用代理，避免eastmoney DNS污染"""
    orig = requests.Session.__init__
    def _init(self, *a, **kw):
        orig(self, *a, **kw)
        self.trust_env = False
    requests.Session.__init__ = _init
    try:
        yield
    finally:
        requests.Session.__init__ = orig

def _safe_float(val) -> float:
    """安全转换为 float"""
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def get_xxx(symbol: str = "", date: str = "") -> DataResult:
    """
    获取{功能描述}。

    数据源: akshare {api_name}
    实时性: {realtime | end_of_day | 非实时，收盘后更新}
    历史查询: {支持 | 不支持}
    缓存: {有/无}缓存

    Args:
        symbol: 股票代码（如 "000001"）
        date: 交易日期 YYYYMMDD

    Returns:
        DataResult，data 为 [DomainData.to_dict(), ...]
    """
    try:
        with _no_proxy():
            df = ak.{api_name}(...)
    except _NETWORK_ERRORS as e:
        raise DataFetchError("akshare", "{api_name}", str(e), "network") from e
    except Exception as e:
        raise DataFetchError("akshare", "{api_name}", str(e), "data") from e

    if df is None or df.empty:
        raise DataFetchError("akshare", "{api_name}", f"无数据: {symbol}", "data")

    rows = []
    for _, row in df.iterrows():
        rows.append(DomainData(
            date=str(row.get("日期", "")).replace("-", ""),
            # ... 其他字段
        ).to_dict())

    rows.sort(key=lambda x: x["date"], reverse=True)
    return DataResult(
        data=rows,
        source="akshare",
        meta={"rows": len(rows), "symbol": symbol}
    )
```

#### 4.3 实现 Tushare Provider（如需要）

```python
# src/finance_data/provider/{domain}/tushare.py
"""{领域描述} - tushare"""
import os
import tushare as ts

from finance_data.provider.{domain}.models import DomainData
from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)

from finance_data.provider.tushare.client import get_pro

def get_xxx(trade_date: str = "", start_date: str = "", end_date: str = "") -> DataResult:
    """..."""
    pro = get_pro()
    try:
        df = pro.{api_name}(
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date,
        )
    except _NETWORK_ERRORS as e:
        raise DataFetchError("tushare", "{api_name}", str(e), "network") from e
    except Exception as e:
        reason = str(e)
        kind = "auth" if "权限" in reason or "token" in reason.lower() else "data"
        raise DataFetchError("tushare", "{api_name}", reason, kind) from e

    if df is None or df.empty:
        raise DataFetchError("tushare", "{api_name}",
                           f"无数据: trade_date={trade_date}", "data")

    rows = []
    for _, row in df.iterrows():
        rows.append(DomainData(
            date=str(row.get("trade_date", "")).replace("-", ""),
            # ... 其他字段
        ).to_dict())

    rows.sort(key=lambda x: x["date"], reverse=True)
    return DataResult(data=rows, source="tushare",
                     meta={"rows": len(rows), "trade_date": trade_date})
```

#### 4.4 导出

```python
# src/finance_data/provider/{domain}/__init__.py
from finance_data.provider.{domain}.akshare import get_xxx as ak_xxx
from finance_data.provider.{domain}.tushare import get_xxx as ts_xxx
```

### Step 5: 添加 MCP Tool

在 `src/finance_data/mcp/server.py` 中添加：

```python
from finance_data.provider.{domain}.akshare import get_xxx as ak_xxx
from finance_data.provider.{domain}.tushare import get_xxx as ts_xxx

@mcp.tool()
async def tool_get_xxx(
    symbol: str = "",
    date: str = "",
) -> str:
    """
    获取{功能描述}。

    数据源: {akshare | tushare | akshare+tushare}
    实时性: {realtime | 非实时，收盘后约15:30更新 | 收盘后16:00}
    历史查询: {支持日期范围 | 仅支持单日 | 不支持}
    缓存: {有20分钟缓存 | 无缓存}

    Args:
        symbol: 股票代码（如 "000001"）
        date: 交易日期 YYYYMMDD

    Returns:
        JSON 列表，每条包含: date, ...

    Note:
        {其他说明}
    """
    # 根据 priority 确定 provider 顺序
    providers = [
        ("akshare", ak_xxx),
        ("tushare", ts_xxx),
    ] if "{both|akshare+tushare}" else [("akshare", ak_xxx)]

    errors = []
    for name, fn in providers:
        try:
            return _to_json(fn(symbol=symbol, date=date))
        except Exception as e:
            logger.warning(f"{name} get_xxx 失败: {e}")
            errors.append(str(e))

    return json.dumps({"error": f"所有数据源均失败: {errors}"}, ensure_ascii=False)
```

### Step 6: 编写测试

```python
# tests/provider/{domain}/test_akshare.py
import pytest
import pandas as pd
from unittest.mock import patch
from finance_data.provider.{domain}.akshare import get_xxx
from finance_data.provider.types import DataResult, DataFetchError

@pytest.fixture
def mock_df():
    return pd.DataFrame([{
        "日期": "20240301",
        "字段1": 100,
        "字段2": 200,
    }])

def test_get_xxx_returns_data_result(mock_df):
    with patch("finance_data.provider.{domain}.akshare.ak.{api_name}",
               return_value=mock_df):
        result = get_xxx(date="20240301")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1

def test_get_xxx_fields(mock_df):
    with patch("finance_data.provider.{domain}.akshare.ak.{api_name}",
               return_value=mock_df):
        result = get_xxx(date="20240301")
    row = result.data[0]
    assert row["date"] == "20240301"

def test_get_xxx_network_error():
    with patch("finance_data.provider.{domain}.akshare.ak.{api_name}",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_xxx(date="20240301")
    assert exc.value.kind == "network"

def test_get_xxx_empty_raises():
    with patch("finance_data.provider.{domain}.akshare.ak.{api_name}",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            get_xxx(date="20240301")
    assert exc.value.kind == "data"
```

### Step 7: 更新文档

1. **更新 `CLAUDE.md`**：
   - 接口数量 +1
   - 添加新接口到表格

2. **更新 `docs/interface-refactor-plan.md`**：
   - 将新接口添加到 TOOL_REGISTRY

3. **运行测试**：
```bash
.venv/bin/pytest tests/provider/{domain}/ -v
.venv/bin/pytest tests/ -v  # 确认无回归
```

## 校验清单

新增接口后，自动检查：

- [ ] Provider 实现有 `_no_proxy()` context manager（akshare）
- [ ] 错误处理：network error / data error / auth error 分类正确
- [ ] 空数据抛出 `DataFetchError`
- [ ] 数据按 date 倒序排列
- [ ] 单位统一（统一为元）
- [ ] docstring 包含：数据源、实时性、历史查询、返回值
- [ ] 测试覆盖：正常数据、network error、empty data
- [ ] CLAUDE.md 已更新
- [ ] `pytest tests/ -v` 全量通过

## 示例：新增 `get_stock_limit_up` 接口

### 输入
- domain: `pool`
- interface_name: `get_stock_limit_up`
- description: "获取涨停股池（首板/连板检测）"
- data_source: `akshare` only
- priority: `akshare`

### 执行结果

1. **元数据**:
```python
ToolMeta(
    name="tool_get_stock_limit_up",
    domain="pool",
    entity="stock",
    scope="daily",
    data_freshness="end_of_day",
    update_timing="T+1_15:30",
    supports_history=False,
    source="akshare",
    source_priority="akshare",
    api_name="stock_zt_pool_em",
    limitations=["仅支持A股"]
)
```

2. **文件变更**:
- 修改现有 `pool/akshare.py` 添加 `get_stock_limit_up`
- 修改 `pool/__init__.py` 导出
- 修改 `mcp/server.py` 添加 `tool_get_stock_limit_up`
- 更新 `CLAUDE.md`
- 添加测试

---

## 常见陷阱

1. **单位不一致**: akshare 有些数据用 亿元，有些用 元，统一转换
2. **SZSE bug**: `stock_margin_detail_szse` 有 openpyxl bug，仅用 SSE
3. **eastmoney DNS**: 使用 `_no_proxy()` 禁用代理
4. **tushare token**: 优先从环境变量读取，错误信息清晰
5. **空数据**: 必须 raise `DataFetchError`，不能返回空列表
