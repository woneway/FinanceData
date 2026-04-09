# FinanceData Phase 1 实施计划：ToolSpec 真相源统一

**日期**: 2026-04-09
**状态**: 已确认
**对应总方案**: `docs/plans/2026-04-09-architecture-upgrade-delivery-validation.md`
**阶段目标**: 引入统一 `ToolSpec` 注册中心，收敛 MCP、dashboard、health、前端工具参数等平行配置，建立后续 CLI、verify、health 统一演进的基础。

---

## 1. 阶段目标

阶段一只解决一个核心问题：

> 同一个工具的定义必须只有一份真相源。

本阶段完成后，以下能力必须从 `ToolSpec` 派生，而不再各自维护平行配置：

- MCP tool 基本元信息
- dashboard `/api/tools`
- dashboard invoke 的 service 目标
- health probe 的 provider 映射与 probe 参数
- 前端工具参数表单

本阶段**不做**：

- CLI 交付层
- 完整 verify 总入口
- 全量动态注册 MCP tools
- provider 行为语义重构

本阶段重点是先把真相源收敛，再进行能力扩展。

---

## 2. 目标架构

新增模块：

```text
src/finance_data/tool_specs/
  __init__.py
  models.py
  registry.py
  adapters.py
  validators.py
```

职责：

- `models.py`
  定义 `ToolSpec` / `ToolParamSpec` / `ProviderSpec` / `ProbeSpec`
- `registry.py`
  注册所有工具
- `adapters.py`
  提供给 MCP、dashboard、health 的兼容查询函数
- `validators.py`
  做 ToolSpec 与现有代码的一致性校验

过渡期允许 MCP 仍保留显式函数定义，但这些函数的参数描述、service target、provider 列表必须来自 `ToolSpec`。

---

## 3. 统一数据模型设计

### 3.1 ToolParamSpec

至少包含：

- `name`
- `required`
- `default`
- `description`
- `example`
- `aliases`

用途：

- 前端渲染参数表单
- CLI 生成参数定义
- dashboard provider 调用时做参数名映射

### 3.2 ProviderSpec

至少包含：

- `name`
- `class_path`
- `method_name`
- `available_if`
- `notes`

用途：

- health probe 动态枚举 provider
- dashboard compare / direct provider invoke

### 3.3 ProbeSpec

至少包含：

- `default_params`
- `timeout_sec`
- `min_records`
- `required_fields`
- `consistency_enabled`

用途：

- health probe
- selected smoke

### 3.4 ToolSpec

至少包含：

- `name`
- `description`
- `domain`
- `params`
- `return_fields`
- `service_module`
- `service_object`
- `service_method`
- `providers`
- `probe`
- `metadata`

---

## 4. 实施任务

### Task 1：建立 ToolSpec 基础模型

**Files**

- Create: `src/finance_data/tool_specs/__init__.py`
- Create: `src/finance_data/tool_specs/models.py`

**要求**

- 模型能表达参数、provider、probe、service target
- 保持 Python 层易于消费，不引入复杂元编程

**验收**

- 可以完整描述现有一个工具，例如 `tool_get_realtime_quote`

---

### Task 2：建立 ToolSpec 注册表

**Files**

- Create: `src/finance_data/tool_specs/registry.py`

**要求**

- 先把当前已暴露工具全部注册进去
- 采用手写 registry，不做自动发现
- 注册表顺序应与工具对外暴露顺序一致

**验收**

- 所有现有 tool 都能在 registry 中找到

---

### Task 3：建立 ToolSpec 适配层

**Files**

- Create: `src/finance_data/tool_specs/adapters.py`

**要求**

提供统一函数，供现有模块调用：

- `get_tool_spec(name)`
- `list_tool_specs()`
- `get_tool_params(name)`
- `get_tool_service_target(name)`
- `get_tool_providers(name)`
- `get_tool_probe(name)`

**验收**

- dashboard 不再自己维护工具参数与 service target

---

### Task 4：收敛 dashboard `/api/tools`

**Files**

- Modify: `src/finance_data/dashboard/app.py`
- Modify: `src/finance_data/dashboard/models.py`

**要求**

- `/api/tools` 直接从 `ToolSpec` 返回
- 不再从多个来源拼装工具事实
- `ToolInfo.params` 来自 ToolSpec

**验收**

- 前端参数表单完全依赖 `/api/tools`

---

### Task 5：收敛 dashboard invoke

**Files**

- Modify: `src/finance_data/dashboard/app.py`

**要求**

- 删除或废弃 `_INVOKE_MAP`
- invoke 的 service 目标来自 ToolSpec
- provider 直连的 method/class 映射来自 ToolSpec
- 参数 alias 规则来自 `ToolParamSpec.aliases`

**验收**

- dashboard invoke 不再维护独立 service 目标表

---

### Task 6：收敛 health probe

**Files**

- Modify: `src/finance_data/dashboard/health.py`

**要求**

- 删除或废弃 `_TOOL_PROVIDERS`
- provider 列表、probe 参数来自 ToolSpec
- 保留现有 health engine 结构，不做大重写

**验收**

- health probe 不再维护独立工具配置

---

### Task 7：建立 ToolSpec 一致性校验

**Files**

- Create: `src/finance_data/tool_specs/validators.py`
- Create: `tests/tool_specs/test_registry_consistency.py`

**检查项**

- 所有 MCP tool 都在 ToolSpec 注册
- ToolSpec 指向的 service target 存在
- probe 参数能通过 MCP 签名校验
- dashboard `/api/tools` 返回参数与 ToolSpec 一致

**验收**

- 一致性测试通过

---

### Task 8：回归与 smoke

**Files**

- Modify: `tests/dashboard/test_api.py`
- Modify: `tests/test_mcp_server.py`
- Create: `tests/tool_specs/test_dashboard_alignment.py`

**目标**

- 证明 ToolSpec 成为真相源后，dashboard 与 MCP 没有断链

---

## 5. 分批实施顺序

建议严格按以下顺序提交：

1. `tool_specs/models.py` + `tool_specs/registry.py`
2. `tool_specs/adapters.py`
3. dashboard `/api/tools`
4. dashboard invoke
5. health probe
6. validators + tests

每一步都应独立提交、独立回归。

---

## 6. 验收标准

阶段一完成的标准：

- 同一工具在系统中只有一份结构化定义
- dashboard 参数表单来自 ToolSpec
- dashboard invoke 的 service target 来自 ToolSpec
- health probe 的 provider/probe 参数来自 ToolSpec
- MCP tool 与 ToolSpec 一致性可测试
- 引入 ToolSpec 后，现有核心测试不回退

---

## 7. 失败后的修复闭环

阶段一实施中如果发现问题，统一按以下流程处理：

1. 归类：是 ToolSpec 建模问题、适配层问题，还是旧调用链残留问题
2. 先加失败测试
3. 修复根因
4. 跑受影响模块测试
5. 跑阶段一全量回归
6. 更新实施文档中的已知风险

不允许直接在 dashboard 或前端加新的局部硬编码绕过问题。

---

## 8. 阶段一完成后的直接收益

- 后续 CLI 可以直接复用 ToolSpec
- verify 可以围绕 ToolSpec 做一致性检查
- 新增接口时，不再需要在 dashboard、health、前端分别手动补配置
- 工具定义漂移问题会明显下降

---

## 9. 阶段一完成后的下一步

阶段一完成后，立即进入阶段二：

- 新建正式 CLI 入口
- CLI 完全复用 ToolSpec + service
- 建立 MCP / CLI / dashboard 的统一调用与观测模型
