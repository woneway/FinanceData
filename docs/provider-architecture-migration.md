# Provider 架构迁移方案

## 新架构设计

### 四层结构

```
finance_data/
├── interface/           # Protocol 定义 + models（零依赖，契约层）
│   └── <domain>/
│       ├── history.py   # XxxHistoryProtocol + models
│       └── realtime.py  # XxxRealtimeProtocol + models
├── provider/            # 具体实现（内部，不对外暴露）
│   ├── akshare/
│   │   └── <domain>/
│   │       ├── history.py
│   │       └── realtime.py
│   └── tushare/
│       └── <domain>/
│           ├── history.py
│           └── realtime.py
├── service/             # 统一对外入口（组装 dispatcher，处理缓存、降级、默认值）
│   └── <domain>.py
└── mcp/
    └── server.py        # 调用 service 层，不感知 provider
```

### 层间依赖方向

```
mcp → service → interface ← provider
```

- `interface/` 不依赖任何内部模块
- `provider/` 只依赖 `interface/`
- `service/` 依赖 `interface/` + `provider/`（唯一知道具体 provider 的地方）
- `mcp/` 只依赖 `service/`

---

## 命名规范

### 接口类型后缀

| 类型 | 后缀 | 说明 |
|------|------|------|
| 实时数据 | `_realtime` | 盘中实时更新，无 date 参数 |
| 历史数据 | `_history` | 支持 date 参数查询，不传则返回最新一天 |

### MCP tool 命名

`tool_get_<domain>_<entity>_<realtime|history>`

Protocol 函数名去掉 `tool_` 前缀即为 service 层函数名。

---

## Provider 降级规则

```python
# service/<domain>.py
providers = [AkshareXxx()]          # akshare 无需 token，始终注册

if os.getenv("TUSHARE_TOKEN"):
    providers.append(TushareXxx())  # tushare 按需注册

dispatcher = XxxDispatcher(providers=providers)
```

---

## 各层职责

| 层 | 职责 |
|---|---|
| `interface/` | Protocol 定义、入参/出参 models |
| `provider/akshare/` | akshare 实现，返回 DataResult |
| `provider/tushare/` | tushare 实现，返回 DataResult |
| `service/` | dispatcher 实例化、provider 降级、缓存、date 默认值 |
| `mcp/server.py` | 调用 service，封装为 MCP tool |

---

## Market 域迁移示例（参考模板）

### 迁移前

```
provider/market/
├── akshare.py   # get_market_stats()
├── tushare.py   # get_market_stats()
└── models.py    # MarketStats

mcp/server.py    # tool_get_market_stats_daily
registry.py      # "tool_get_market_stats_daily": ToolMeta(...)
```

### 迁移后

```
interface/market/
└── realtime.py              # MarketRealtimeProtocol + MarketStats

provider/akshare/market/
└── realtime.py              # AkshareMarketRealtime

service/
└── market.py                # market_realtime dispatcher 实例

mcp/server.py                # tool_get_market_stats_realtime → service
registry.py                  # "tool_get_market_stats_realtime": ToolMeta(REALTIME)
```

### Step 1：定义 interface

```python
# interface/market/realtime.py
from typing import Protocol
from finance_data.interface.types import DataResult
from dataclasses import dataclass

@dataclass
class MarketStats:
    date: str
    up_count: int
    down_count: int
    flat_count: int
    total_count: int
    total_amount: float | None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

class MarketRealtimeProtocol(Protocol):
    def get_market_stats_realtime(self) -> DataResult: ...
```

### Step 2：实现 provider

```python
# provider/akshare/market/realtime.py
import akshare as ak
from finance_data.interface.market.realtime import MarketRealtimeProtocol, MarketStats
from finance_data.interface.types import DataResult, DataFetchError

class AkshareMarketRealtime:
    def get_market_stats_realtime(self) -> DataResult:
        ...
```

### Step 3：组装 service

```python
# service/market.py
import os
from finance_data.interface.market.realtime import MarketRealtimeProtocol, DataResult
from finance_data.provider.akshare.market.realtime import AkshareMarketRealtime

class _MarketRealtimeDispatcher:
    def __init__(self, providers: list[MarketRealtimeProtocol]):
        self._providers = providers

    def get_market_stats_realtime(self) -> DataResult:
        for p in self._providers:
            try:
                return p.get_market_stats_realtime()
            except Exception as e:
                logger.warning(f"{type(p).__name__} 失败: {e}")
        raise DataFetchError("all", "get_market_stats_realtime", "所有数据源均失败")

def _build_market_realtime() -> _MarketRealtimeDispatcher:
    providers: list[MarketRealtimeProtocol] = [AkshareMarketRealtime()]
    # tushare 暂无等效接口，不注册
    return _MarketRealtimeDispatcher(providers=providers)

market_realtime = _build_market_realtime()
```

### Step 4：更新 MCP server

```python
# mcp/server.py
from finance_data.service.market import market_realtime

@mcp.tool()
async def tool_get_market_stats_realtime() -> str:
    """
    获取当日市场涨跌家数统计（盘中实时）。

    数据源: 仅 akshare
    实时性: 盘中实时（T+0）
    历史查询: 不支持

    Returns:
        JSON 列表，包含 date、up_count、down_count、flat_count、total_amount
    """
    try:
        return _to_json(market_realtime.get_market_stats_realtime())
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
```

### Step 5：更新 registry

```python
"tool_get_market_stats_realtime": ToolMeta(
    name="tool_get_market_stats_realtime",
    data_freshness=DataFreshness.REALTIME,
    update_timing=UpdateTiming.T_PLUS_0,
    supports_history=False,
    source=DataSource.AKSHARE,
    ...
)
```

### Step 6：删除旧文件

```bash
rm provider/market/akshare.py
rm provider/market/tushare.py
rm provider/market/models.py
```

---

## 迁移检查清单

每个 domain 迁移完成后验证：

- [ ] `interface/<domain>/` Protocol 定义完整，入参/出参类型明确
- [ ] `provider/akshare/<domain>/` 实现满足 Protocol（mypy 无报错）
- [ ] `provider/tushare/<domain>/` 实现满足 Protocol（如有）
- [ ] `service/<domain>.py` provider 降级逻辑正确
- [ ] `mcp/server.py` tool 命名更新，调用 service 层
- [ ] `registry.py` ToolMeta 更新，`data_freshness` 准确
- [ ] 旧 `provider/<domain>/` 文件已删除
- [ ] `CLAUDE.md` 接口列表同步更新
- [ ] 测试通过：`pytest tests/ -v`
