## Context

Explore 阶段已精确摸清两个超大文件的内部结构与外部依赖：

- `mcp/server.py` 1263 行：38 行 service import + 2 个 helper（`_to_json`、`_invoke_tool_json`） + 48 个 `@mcp.tool()` 函数。源码顺序与 `TOOL_SPEC_REGISTRY` 中 ToolSpec 顺序**完全一致**（这是设计意图：MCP 工具列表与 ToolSpec 列表对外是同一个顺序）。
- `tool_specs/registry.py` 968 行：5 个工厂 helper + 一个 `TOOL_SPEC_REGISTRY = OrderedDict(...)` 巨型字面量。
- 反向依赖只有 4 个调用点（mcp_server.py 1 处 + tool_specs/__init__.py 1 处 + adapters.py 内部 1 处 + tests 4 处 patch）。
- 4 处 patch 路径形如 `finance_data.mcp.server.<service_name>.<method>`（如 `stock_history`、`suspend`、`hot_rank`），依赖 server.py 顶部 `from finance_data.service.xxx import <service_name>` 把 service 实例挂在自己名字空间。

source-of-truth 映射：

| 层级 | Source of truth | 本 change 操作 |
| --- | --- | --- |
| MCP tool 注册顺序 | `TOOL_SPEC_REGISTRY` OrderedDict | 由「按确定顺序 import 14 个 tools 子模块」严格保持 |
| MCP 单例 | `mcp = FastMCP("finance-data")` | 抽到 `mcp/_app.py` 单例 |
| ToolSpec 字面量 | 14 个 `tool_specs/registry/<domain>.py` | 由 `registry/__init__.py` 拼接 |
| service 名字空间兼容 | `mcp/server.py` re-export 全部 service | 显式 `from ... import *` 风格列出 |
| 测试 patch 路径 | `finance_data.mcp.server.<service>.<method>` | 由 server.py re-export 保兼容 |

## Goals / Non-Goals

**Goals:**
- 两个 800+ 行文件按 14 domain 物理拆分到 28 个 < 200 行新文件。
- 行为零变更：48 个 tool 名称 / 签名 / docstring / 返回 JSON 全部不变。
- TOOL_SPEC_REGISTRY 顺序严格保持。
- 全部外部 import 入口 + 测试 mock 路径兼容。
- 守护测试锁定「mcp 注册顺序 = ToolSpec 顺序」不变量，未来任何拆分 / 合并都受其保护。

**Non-Goals:**
- 不修改 service / provider / interface / client / cache / config / cli / dashboard / verify。
- 不调整 ToolSpec 字段。
- 不调整 MCP tool 签名 / docstring / 返回字段。
- 不动 `client.py`（命名统一留待阶段 5）。
- 不引入「自动注册装饰器」之类抽象（与 retroactive-tushare-stk-factor-pro design 中拒绝「完全动态生成 MCP 函数」的 Decision 一致）。

## Decisions

### 1. 抽 FastMCP 单例与 helper 到 `_app.py` 而非保留在 server.py

**理由**：
- 14 个 `mcp/tools/<domain>.py` 都需要 `from ... import mcp` 与 `_invoke_tool_json` helper。
- 若保留在 server.py，会形成「server.py → tools/<domain>.py → server.py」循环 import。
- 抽到独立 `_app.py` 模块，`tools/<domain>.py` 与 `server.py` 都 import 它，无循环。
- 命名 `_app.py` 加下划线前缀表示「内部模块，外部不应直接 import」。

### 2. server.py 收敛为「aggregator + service re-export」

**实现形态**：
```python
# server.py（拆分后约 50 行）
from finance_data.mcp._app import mcp  # noqa: F401, 仍导出
# 按确定顺序 import 14 个 tools 子模块以触发 @mcp.tool() 注册
from finance_data.mcp.tools import stock, kline, quote, index, board, fundamental, \
    cashflow, lhb, pool, north_flow, margin, market, technical, fund_flow  # noqa: F401
# re-export 全部 service 名字以兼容测试 patch 路径
from finance_data.service.stock import stock_history, stock_basic_list  # noqa: F401
from finance_data.service.kline import (
    daily_kline_history, weekly_kline_history,
    monthly_kline_history, minute_kline_history,
)  # noqa: F401
... # 等等，与原 server.py 顶部 service import 完全一致
```

**理由**：
- 测试 patch 必须保留兼容（`patch("finance_data.mcp.server.stock_history.get_stock_info_history")`）。改测试虽可，但违反 retroactive-stk 中 design Decision 3「retroactive 不重写已实施的代码」精神，本 change 同样应零修改测试。
- re-export 名字与原 server.py 行 9-37 的 import 语句一一对应，确保兼容面 100% 覆盖。
- 14 个 tools 子模块的 import 顺序必须明确（不用 `from finance_data.mcp.tools import *`），保证注册顺序确定。

### 3. ToolSpec registry 拆分采用「子模块定义 SPECS list + __init__ 拼接 OrderedDict」

**实现形态**：
```python
# tool_specs/registry/_factories.py（5 个 helper）
def _param(...): ...
def _provider(...): ...
def _service(...): ...
def _probe(...): ...
def _meta(...): ...
```
```python
# tool_specs/registry/<domain>.py
from collections.abc import Sequence
from finance_data.tool_specs.models import ToolSpec
from finance_data.tool_specs.registry._factories import _param, _provider, _service, _probe, _meta

SPECS: Sequence[ToolSpec] = [
    ToolSpec(name="...", domain="...", ...),
    ...
]
```
```python
# tool_specs/registry/__init__.py
from collections import OrderedDict
from finance_data.tool_specs.registry import (
    stock, kline, quote, index, board, fundamental,
    cashflow, lhb, pool, north_flow, margin, market,
    technical, fund_flow,
)

_DOMAIN_ORDER = (stock, kline, quote, index, board, fundamental, cashflow,
                 lhb, pool, north_flow, margin, market, technical, fund_flow)

TOOL_SPEC_REGISTRY: "OrderedDict[str, ToolSpec]" = OrderedDict(
    (spec.name, spec) for module in _DOMAIN_ORDER for spec in module.SPECS
)
```

**理由**：
- `__init__.py` 明确写 `_DOMAIN_ORDER` 元组，肉眼可见的拼接顺序。
- 子模块只暴露 `SPECS: list[ToolSpec]`，简洁。
- helper 集中到 `_factories.py`，14 个 domain 共享。
- 删除原 `registry.py` 文件（与 `registry/` 包同名会导致 import 冲突）。

### 4. 14 个 domain 的具体顺序与原 1264 行 server.py 完全一致

按 Explore 报告，原 server.py 中 48 个 tool 的源码顺序对应：
```
stock(1), kline(3), quote(1), index(2), board(1), fundamental(3), cashflow(1),
calendar(1), lhb(5), north_flow(1), margin(2), suspend(1), hot_rank(2), pool(4),
board_member_kline(2), lhb_inst(1), hm(2), pool_extra(2), market_misc(2),
daily_market(3), pool_extra2(1), stock_basic(1), technical(1), fund_flow(2),
kline_minute(1)
```

但这并非 14 domain 的「连续段」—— 各 domain 在源码中是穿插出现的（例如 board 出现在第 5 个 tool，但 board_member 出现在第 35 个 tool 附近）。

**对策**：
- 拆分时保持 ToolSpec 字面量在 `registry.py` 内的**字面顺序**（即 `_DOMAIN_ORDER` 拼接出的顺序与原 OrderedDict 的 keys 顺序完全一致）。
- 但**实际操作**：把 14 个 domain 的全部 ToolSpec 集中到对应 `<domain>.py`（按 domain 字段分组），然后 `_DOMAIN_ORDER` 顺序 = 该 ToolSpec 在原 registry.py 中**首次出现位置**的顺序。
- 这会改变 OrderedDict 的 keys 顺序 → 与 spec 第 2 条 Requirement「拆分前后 tool 名称集合稳定 + 顺序保持完全相同」冲突。

**重新决策**：
- 选项 A：保持原顺序（按源码内顺序），但同 domain 的 ToolSpec 散落到不同位置 → 不能用「按 domain 集中到一个文件」。
- 选项 B：接受顺序变更（按 domain 集中），并在 spec 中放宽顺序约束（不要求 keys 顺序与原一致，只要求拆分前后 mcp 注册顺序 = TOOL_SPEC_REGISTRY 顺序一致）。

**选择 B**。

**理由**：
- 选项 A 失去了「按 domain 拆分」的核心收益（同 domain ToolSpec 仍然散落在 14 个文件中，只是路径变了）。
- 选项 B 保留拆分收益，且对外接口稳定性影响极小：dashboard 工具列表展示顺序变化，但工具集合不变。
- 守护测试约束「mcp 注册顺序 = TOOL_SPEC_REGISTRY 顺序」是真正重要的不变量；「拆分前后顺序完全一致」是过度承诺。
- 对应修改：proposal 中「OrderedDict 顺序保持与原 registry.py 完全一致」说法收回；spec Scenario「拆分前后 tool 名称集合稳定」改为「集合稳定（顺序可变，但前后两次拆分操作必须可重现同一顺序）」。

### 5. 守护测试 `test_tools_layout.py` 双向锁定

测试要做两件事：
1. **集合一致性**：`set(mcp_registered_tool_names) == set(TOOL_SPEC_REGISTRY.keys())`，集合必须完全相等（48 个）。
2. **顺序一致性**：`list(mcp_registered_tool_names) == list(TOOL_SPEC_REGISTRY.keys())`，列表顺序必须完全相等。

**理由**：
- 集合一致性防止「ToolSpec 注册了但 MCP 没注册」或反之。
- 顺序一致性防止 `_DOMAIN_ORDER` 与 `mcp/tools/__init__.py` 的 import 顺序错位。
- 两者一起强制：未来新增 tool 必须同时在 `registry/<domain>.py` 与 `mcp/tools/<domain>.py` 加，且 14 个 domain 在两处的顺序保持一致。

**实现挑战**：FastMCP 是否暴露「list 已注册 tool」API？需要 explore 验证。若无，可用 `mcp._tool_manager` 内部状态（当前 fastmcp 实现）或 `await mcp.list_tools()`（标准 MCP 方法）。

### 6. 不修改 `tests/test_mcp_server.py` 的 4 处 patch

**理由**：
- patch 路径 `finance_data.mcp.server.stock_history.get_stock_info_history` 依赖 server.py 顶部 import `from finance_data.service.stock import stock_history`。
- 拆分后 server.py 必须保留这些 import（用 noqa F401 抑制 lint），即「re-export 全部 service 名字」。
- 这是 spec 第 3 条 Requirement「拆分必须保留外部 import 入口与测试 mock 路径」的硬约束。

## Source-of-Truth 映射

| 行为 | 实现承担方 |
| --- | --- |
| FastMCP 单例 | `mcp/_app.py` |
| 工具注册（@mcp.tool 装饰） | `mcp/tools/<domain>.py` |
| 共享 helper（_to_json / _invoke_tool_json） | `mcp/_app.py` |
| MCP 入口（mcp_server.py 消费） | `mcp/server.py` re-export `mcp` |
| 测试 patch 路径 | `mcp/server.py` re-export 全部 service 名字 |
| ToolSpec 字面量 | `tool_specs/registry/<domain>.py`（每个 domain 一个 SPECS list） |
| ToolSpec 拼接为 OrderedDict | `tool_specs/registry/__init__.py` 按 `_DOMAIN_ORDER` 拼接 |
| ToolSpec 工厂 helper | `tool_specs/registry/_factories.py` |
| TOOL_SPEC_REGISTRY 对外入口 | 仍为 `from finance_data.tool_specs.registry import TOOL_SPEC_REGISTRY`（包路径不变） |

## Risks / Trade-offs

- [Risk] 拆分后 `TOOL_SPEC_REGISTRY` keys 顺序与原不一致（按 domain 集中后，跨 domain 的相对顺序变化）。  
  → Mitigation: design Decision 4 已明确选择此 trade-off；下游 dashboard 顺序可能微变，但工具集合不变；spec 守护测试只锁「mcp 顺序 = registry 顺序」一致性，不要求与历史一致。

- [Risk] FastMCP 不暴露「list 已注册 tool」公开 API，守护测试无法实施。  
  → Mitigation: 调研 fastmcp 实现，若必要可访问 `mcp._tool_manager._tools` 等内部属性，或用 `asyncio.run(mcp.list_tools())`。守护测试合入前必须确认实现可行。

- [Risk] 14 个 `tools/<domain>.py` 各自 `@mcp.tool()` 装饰器的副作用（注册到 `_app.mcp`）依赖 import 时机。如果 `mcp/server.py` 的 import 顺序错误，注册顺序就会错。  
  → Mitigation: server.py 用显式列出的 import 而非 `from .tools import *`；守护测试锁定顺序。

- [Risk] re-export 列表庞大（38 行 service import），lint 规则可能告警未使用。  
  → Mitigation: `# noqa: F401` 标注所有 re-export 行；CLAUDE.md 注释说明用途。

- [Risk] `tools/<domain>.py` 使用 `_invoke_tool_json(tool_name, params)` helper 时需要传入 tool name 字符串，与原 server.py 形态一致；但若 helper 签名要求传入函数对象，会破坏一致性。  
  → Mitigation: 严格保留原 helper 签名（`_invoke_tool_json(tool: str, params: dict) -> str`）。

- [Risk] 14 个 domain 拆分后的实际行数若仍超 800 行（如 lhb 含 8 个 tool 可能 ~300 行，pool 含 7 个 tool ~250 行），整体不会超。但若未来某 domain 接口暴增，需进一步拆分（如 lhb/detail.py + lhb/stat.py）。  
  → Mitigation: 目前 14 个 domain 拆分后预计每个文件 50-300 行，远低于 800；未来若超标再开新 change 二级拆分。

## Migration Plan（守护测试先行）

1. **守护测试先行**：在拆分前先写 `tests/mcp/test_tools_layout.py`，断言「mcp 已注册的 tool 名称列表 = TOOL_SPEC_REGISTRY keys 列表」（集合 + 顺序）。在当前未拆分代码下跑通。
2. **新建 `mcp/_app.py`**：抽 FastMCP 单例 + 2 个 helper，server.py 暂不动。验证 import 通过。
3. **新建 `tool_specs/registry/_factories.py`**：搬 5 个 helper。`registry.py` 暂用 `from .registry._factories import _param ...` 引用（兼容过渡）。
4. **拆 `tool_specs/registry/<domain>.py`**：14 个 domain 各暴露 `SPECS: list[ToolSpec]`。新建 `registry/__init__.py` 用 `_DOMAIN_ORDER` 拼接 OrderedDict。删除原 `registry.py` 文件。验证 `from finance_data.tool_specs.registry import TOOL_SPEC_REGISTRY` 仍 work，长度 = 48。
5. **拆 `mcp/tools/<domain>.py`**：14 个 domain 各从 `_app` import `mcp` + helper，定义 `@mcp.tool()` 函数（从原 server.py 整段搬过来）。
6. **重写 `mcp/server.py`**：变为 aggregator，按确定顺序 import 14 个 tools 子模块 + re-export 全部 service 名字。
7. **跑全量 pytest**：必须 412 passed + 守护测试通过。
8. **archive**。

回滚策略：
- 步骤 1 守护测试合入后即使后续步骤失败也无害。
- 步骤 2-7 按文件粒度可单独 `git revert`。
- 最后整体 squash 到一个 commit（拆分是原子动作，分散 commit 历史无意义）—— 留待 commit 时决策。

## Open Questions

- FastMCP 内部 `_tool_manager._tools` 属性是否稳定？若不稳定需要寻找替代。
- 是否需要把 `_DOMAIN_ORDER` 暴露为常量供其他模块使用？暂不暴露（YAGNI）。
- 拆分后 server.py 仍是 ~50 行的「巨型 re-export」，是否值得进一步拆 re-export 到独立文件？暂不拆（re-export 是兼容层，集中在 server.py 反而便于一眼看清兼容面）。
