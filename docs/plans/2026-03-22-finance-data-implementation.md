# FinanceData Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 搭建 FinanceData 项目骨架，并实现首个接口 `get_stock_info`，验证完整链路（provider → MCP tool + Python library）。

**Architecture:** Provider 分层架构。`provider/akshare/` 和 `provider/tushare/` 各自封装数据源，`mcp/server.py` 做薄 MCP 适配，provider 层同时支持直接 Python import。

**Tech Stack:** Python 3.11+, akshare, tushare, pydantic, fastmcp, pytest

---

## 前置条件

项目目录已创建：`~/ai/projects/FinanceData/`
设计文档已在：`docs/plans/2026-03-22-finance-data-design.md`

---

### Task 1: 初始化项目结构

**Files:**
- Create: `pyproject.toml`
- Create: `src/finance_data/__init__.py`
- Create: `src/finance_data/provider/__init__.py`
- Create: `src/finance_data/provider/akshare/__init__.py`
- Create: `src/finance_data/provider/tushare/__init__.py`
- Create: `src/finance_data/mcp/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/provider/__init__.py`
- Create: `mcp_server.py`

**Step 1: 创建 pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "finance-data"
version = "0.1.0"
description = "金融数据服务 - MCP + Python library"
requires-python = ">=3.11"
dependencies = [
    "akshare>=1.0.0",
    "tushare>=1.4.0",
    "pydantic>=2.0.0",
    "fastmcp>=0.1.0",
    "pandas>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.0.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/finance_data"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 2: 创建所有 `__init__.py`（均为空文件）**

```bash
cd ~/ai/projects/FinanceData
mkdir -p src/finance_data/provider/akshare
mkdir -p src/finance_data/provider/tushare
mkdir -p src/finance_data/mcp
mkdir -p tests/provider
touch src/finance_data/__init__.py
touch src/finance_data/provider/__init__.py
touch src/finance_data/provider/akshare/__init__.py
touch src/finance_data/provider/tushare/__init__.py
touch src/finance_data/mcp/__init__.py
touch tests/__init__.py
touch tests/provider/__init__.py
```

**Step 3: 创建 mcp_server.py 占位**

```python
"""MCP 启动入口"""
from finance_data.mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
```

**Step 4: 安装依赖**

```bash
cd ~/ai/projects/FinanceData
pip install -e ".[dev]"
```

Expected: 依赖安装成功，无报错

**Step 5: 验证包可导入**

```bash
python -c "import finance_data; print('OK')"
```

Expected: `OK`

**Step 6: Commit**

```bash
git add .
git commit -m "chore: 初始化项目结构"
```

---

### Task 2: 实现共享类型 types.py

**Files:**
- Create: `src/finance_data/provider/types.py`
- Create: `tests/provider/test_types.py`

**Step 1: 写失败测试**

```python
# tests/provider/test_types.py
from finance_data.provider.types import DataResult, DataFetchError


def test_data_result_basic():
    result = DataResult(
        data=[{"name": "平安银行", "code": "000001"}],
        source="akshare",
        meta={"rows": 1},
    )
    assert result.source == "akshare"
    assert len(result.data) == 1


def test_data_fetch_error_kinds():
    err = DataFetchError(source="akshare", func="get_stock_info", reason="timeout", kind="network")
    assert err.kind == "network"
    assert "akshare" in str(err)


def test_data_fetch_error_invalid_kind():
    import pytest
    with pytest.raises(ValueError):
        DataFetchError(source="akshare", func="foo", reason="x", kind="invalid_kind")
```

**Step 2: 运行测试，确认失败**

```bash
pytest tests/provider/test_types.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: 实现 types.py**

```python
# src/finance_data/provider/types.py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

ErrorKind = Literal["network", "data", "auth", "quota"]
_VALID_KINDS = {"network", "data", "auth", "quota"}


@dataclass
class DataResult:
    """所有 provider 函数的统一返回类型"""
    data: List[Dict[str, Any]]
    source: str
    meta: Dict[str, Any] = field(default_factory=dict)


class DataFetchError(Exception):
    """数据获取错误"""

    def __init__(self, source: str, func: str, reason: str, kind: str):
        if kind not in _VALID_KINDS:
            raise ValueError(f"kind 必须是 {_VALID_KINDS} 之一，got: {kind!r}")
        self.source = source
        self.func = func
        self.reason = reason
        self.kind = kind
        super().__init__(f"[{source}] {func} 失败 ({kind}): {reason}")
```

**Step 4: 运行测试，确认通过**

```bash
pytest tests/provider/test_types.py -v
```

Expected: 3 passed

**Step 5: Commit**

```bash
git add src/finance_data/provider/types.py tests/provider/test_types.py
git commit -m "feat: 添加共享类型 DataResult 和 DataFetchError"
```

---

### Task 3: 实现 get_stock_info provider

**Files:**
- Create: `src/finance_data/provider/akshare/stock.py`
- Create: `tests/provider/test_stock.py`

**Step 1: 写失败测试**

```python
# tests/provider/test_stock.py
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from finance_data.provider.akshare.stock import get_stock_info
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_akshare_stock_info():
    """mock akshare 返回的 DataFrame"""
    return pd.DataFrame([
        {"item": "股票代码", "value": "000001"},
        {"item": "股票简称", "value": "平安银行"},
        {"item": "行业", "value": "银行"},
        {"item": "上市时间", "value": "19910403"},
    ])


def test_get_stock_info_returns_data_result(mock_akshare_stock_info):
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_info_em",
               return_value=mock_akshare_stock_info):
        result = get_stock_info("000001")

    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 4
    assert result.data[0]["item"] == "股票代码"


def test_get_stock_info_meta_contains_rows(mock_akshare_stock_info):
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_info_em",
               return_value=mock_akshare_stock_info):
        result = get_stock_info("000001")

    assert result.meta["rows"] == 4
    assert result.meta["symbol"] == "000001"


def test_get_stock_info_network_error_raises_data_fetch_error():
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_info_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc_info:
            get_stock_info("000001")

    assert exc_info.value.kind == "network"
    assert exc_info.value.source == "akshare"


def test_get_stock_info_data_error_raises_data_fetch_error():
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_info_em",
               side_effect=Exception("股票代码不存在")):
        with pytest.raises(DataFetchError) as exc_info:
            get_stock_info("INVALID")

    assert exc_info.value.kind == "data"
```

**Step 2: 运行测试，确认失败**

```bash
pytest tests/provider/test_stock.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: 实现 stock.py**

```python
# src/finance_data/provider/akshare/stock.py
"""
股票基础信息接口
数据源: akshare
"""
import akshare as ak
from pydantic import BaseModel, Field

from finance_data.provider.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


class StockInfoInput(BaseModel):
    symbol: str = Field(description="股票代码", example="000001")


def get_stock_info(symbol: str) -> DataResult:
    """
    获取个股基本信息。

    Args:
        symbol: 股票代码，如 "000001"

    Returns:
        DataResult，data 为 [{"item": str, "value": str}, ...]

    Raises:
        DataFetchError: 网络错误或数据错误
    """
    try:
        df = ak.stock_individual_info_em(symbol=symbol)
    except _NETWORK_ERRORS as e:
        raise DataFetchError(
            source="akshare",
            func="stock_individual_info_em",
            reason=str(e),
            kind="network",
        ) from e
    except Exception as e:
        raise DataFetchError(
            source="akshare",
            func="stock_individual_info_em",
            reason=str(e),
            kind="data",
        ) from e

    records = df.to_dict(orient="records")

    return DataResult(
        data=records,
        source="akshare",
        meta={"rows": len(records), "symbol": symbol},
    )
```

**Step 4: 运行测试，确认通过**

```bash
pytest tests/provider/test_stock.py -v
```

Expected: 4 passed

**Step 5: Commit**

```bash
git add src/finance_data/provider/akshare/stock.py tests/provider/test_stock.py
git commit -m "feat: 实现 get_stock_info provider (akshare)"
```

---

### Task 4: 实现 MCP server

**Files:**
- Create: `src/finance_data/mcp/server.py`
- Create: `tests/test_mcp_server.py`

**Step 1: 写失败测试**

```python
# tests/test_mcp_server.py
from unittest.mock import patch
import json
import pytest

from finance_data.provider.types import DataResult, DataFetchError


def test_server_importable():
    """server 模块可以导入"""
    from finance_data.mcp import server
    assert hasattr(server, "mcp")


def test_get_stock_info_tool_success():
    """get_stock_info tool 正常返回 JSON"""
    from finance_data.mcp.server import tool_get_stock_info

    mock_result = DataResult(
        data=[{"item": "股票简称", "value": "平安银行"}],
        source="akshare",
        meta={"rows": 1, "symbol": "000001"},
    )

    with patch("finance_data.mcp.server.get_stock_info", return_value=mock_result):
        import asyncio
        response = asyncio.run(tool_get_stock_info("000001"))

    parsed = json.loads(response)
    assert parsed["source"] == "akshare"
    assert len(parsed["data"]) == 1


def test_get_stock_info_tool_error():
    """get_stock_info tool 错误时返回可读错误信息"""
    from finance_data.mcp.server import tool_get_stock_info

    with patch("finance_data.mcp.server.get_stock_info",
               side_effect=DataFetchError("akshare", "stock_individual_info_em", "timeout", "network")):
        import asyncio
        response = asyncio.run(tool_get_stock_info("000001"))

    assert "错误" in response or "error" in response.lower()
```

**Step 2: 运行测试，确认失败**

```bash
pytest tests/test_mcp_server.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: 实现 server.py**

```python
# src/finance_data/mcp/server.py
"""
MCP 接入层 - 薄封装，不含业务逻辑
"""
import json
import logging

from fastmcp import FastMCP

from finance_data.provider.akshare.stock import get_stock_info
from finance_data.provider.types import DataFetchError

logger = logging.getLogger(__name__)
mcp = FastMCP("finance-data")


@mcp.tool()
async def tool_get_stock_info(symbol: str) -> str:
    """
    获取个股基本信息。

    Args:
        symbol: 股票代码，如 "000001"（平安银行）

    Returns:
        JSON 格式的个股信息，包含股票代码、名称、行业、上市时间等
    """
    try:
        result = get_stock_info(symbol)
        return json.dumps(
            {"data": result.data, "source": result.source, "meta": result.meta},
            ensure_ascii=False,
            indent=2,
        )
    except DataFetchError as e:
        logger.error(f"get_stock_info 失败: {e}")
        return json.dumps({"error": str(e), "kind": e.kind}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"get_stock_info 未知错误: {e}", exc_info=True)
        return json.dumps({"error": f"未知错误: {e}"}, ensure_ascii=False)
```

**Step 4: 运行测试，确认通过**

```bash
pytest tests/test_mcp_server.py -v
```

Expected: 3 passed

**Step 5: Commit**

```bash
git add src/finance_data/mcp/server.py tests/test_mcp_server.py
git commit -m "feat: 实现 MCP server，添加 tool_get_stock_info"
```

---

### Task 5: 完善 mcp_server.py 启动入口

**Files:**
- Modify: `mcp_server.py`

**Step 1: 更新 mcp_server.py**

```python
# mcp_server.py
"""
FinanceData MCP 启动入口

使用方式：
  python mcp_server.py

MCP 配置（Claude Desktop / claude.json）：
  {
    "mcpServers": {
      "finance-data": {
        "command": "python3",
        "args": ["/path/to/FinanceData/mcp_server.py"],
        "env": {
          "TUSHARE_TOKEN": "your_token_here"
        }
      }
    }
  }
"""
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

from finance_data.mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
```

**Step 2: 验证启动不报错（Ctrl+C 退出）**

```bash
python mcp_server.py &
sleep 2
kill %1
```

Expected: 启动无报错

**Step 3: 跑全量测试**

```bash
pytest tests/ -v
```

Expected: 所有测试通过

**Step 4: Commit**

```bash
git add mcp_server.py
git commit -m "chore: 完善 MCP 启动入口，添加配置说明"
```

---

### Task 6: 验证 Python library 接入方式

**Step 1: 验证直接 import 可用**

```bash
python -c "
from finance_data.provider.akshare.stock import get_stock_info
print('import OK')
print('get_stock_info:', get_stock_info.__doc__.strip().split()[0])
"
```

Expected:
```
import OK
get_stock_info: 获取个股基本信息。
```

**Step 2: 真实调用冒烟测试（需要网络）**

```bash
python -c "
from finance_data.provider.akshare.stock import get_stock_info
result = get_stock_info('000001')
print('source:', result.source)
print('rows:', result.meta['rows'])
print('first row:', result.data[0])
"
```

Expected: 输出平安银行的基本信息

**Step 3: Commit**

```bash
git add .
git commit -m "chore: 验证 Python library 接入方式可用"
```

---

### Task 7: 更新 CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

**Step 1: 创建 CLAUDE.md**

```markdown
# FinanceData

金融数据服务，支持 MCP（AI Agent）和 Python library 两种接入方式。

## MCP 配置

```json
{
  "mcpServers": {
    "finance-data": {
      "command": "python3",
      "args": ["/Users/lianwu/ai/projects/FinanceData/mcp_server.py"],
      "env": {
        "TUSHARE_TOKEN": "your_token"
      }
    }
  }
}
```

## 环境变量

- `TUSHARE_TOKEN`：tushare API token（tushare 接口必须）

## 开发

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## 新增接口流程

1. 在 `src/finance_data/provider/akshare/` 或 `tushare/` 下添加函数
2. 在 `tests/provider/` 下添加对应测试
3. 在 `src/finance_data/mcp/server.py` 添加 MCP tool
4. 更新 CLAUDE.md 接口列表

## 当前接口

| Tool | 数据源 | 说明 |
|------|--------|------|
| `get_stock_info` | akshare | 个股基本信息 |
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: 添加 CLAUDE.md"
```

---

## 完成标准

- [ ] `pytest tests/ -v` 全部通过
- [ ] `python -c "from finance_data.provider.akshare.stock import get_stock_info"` 无报错
- [ ] `python mcp_server.py` 启动无报错
- [ ] 真实调用 `get_stock_info("000001")` 返回正确数据
