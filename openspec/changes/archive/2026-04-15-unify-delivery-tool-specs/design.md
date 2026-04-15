## Context

FinanceData 目前有 CLI、MCP、Dashboard API 和前端看板四类交付入口。CLI 与 Dashboard API 已经通过 `tool_specs` 读取工具列表、参数、默认值、provider 列表和 service target；前端看板通过后端 `/api/tools` 动态渲染工具表单。MCP 仍主要是显式函数中手写调用 service，这保证了业务调用最终走 service，但工具契约、默认值、alias 和错误结构仍可能与注册表漂移。

本 change 不涉及新的金融数据源，也不改变任何上游接口映射。source-of-truth 映射如下：

| 层级 | Source of truth | 说明 |
| --- | --- | --- |
| 工具契约 | `ToolSpec` | 工具名、参数、默认值、choices、返回字段、provider 列表、probe、service target |
| 业务语义 | service | 参数业务语义、fallback、缓存、错误归一、provider 调度 |
| 数据语义 | 上游官方接口与 provider 适配 | 本 change 不修改数据字段、单位、更新时间或 provider 策略 |
| 前端表单 | Dashboard `/api/tools` | 由 `ToolSpec` 投影，不维护本地工具参数表 |

## Goals / Non-Goals

**Goals:**
- MCP、CLI、Dashboard API、前端看板统一消费 `ToolSpec` 作为工具契约。
- 所有交付入口最终调用 service，保持 service 是唯一业务真相层。
- MCP 保留显式函数签名，函数体收敛到统一 ToolSpec dispatch helper。
- 参数默认值、alias 归一、service target dispatch 和错误 JSON 在交付层尽量复用同一套逻辑。
- 验证能发现工具在 MCP、CLI、Dashboard、前端契约之间的漂移。

**Non-Goals:**
- 不改 `FinanceData` Python 客户端领域 API；它继续直接调用 service。
- 不新增 provider，不修改 provider 优先级。
- 不改变金融数据字段、单位、更新时间、未完成周期处理方式。
- 不做完全动态生成 MCP 函数，避免削弱 MCP schema 可读性和显式签名。

## Decisions

### 1. 保留显式 MCP 函数签名，函数体走统一 helper

MCP 工具继续保留稳定的函数名、参数签名和 docstring，便于 MCP 客户端生成 schema 和展示参数。每个函数体改为收集参数并调用统一 helper，由 helper 根据工具名读取 `ToolSpec`，应用默认值与 alias 归一，然后按 service target 调用 service。

替代方案是完全动态注册 MCP tools。该方案注册表最统一，但会增加 SDK 兼容风险，也可能降低工具签名和文档质量。当前选择显式签名加统一 dispatch，是兼容性和统一性的折中。

### 2. CLI 和 Dashboard invoke 复用同一套 dispatch 逻辑

CLI 和 Dashboard 已经按 `ToolSpec.service` 调用 service，但存在局部重复的参数处理和 provider 直调逻辑。本 change 应优先抽出交付层共享 helper，降低 CLI、Dashboard、MCP 的实现漂移。

provider 直调仍只作为调试/健康检查能力存在；用户默认调用路径必须走 service dispatcher。provider 直调也必须使用 ToolSpec 中声明的 provider 和参数 alias 规则。

### 3. 前端只消费后端工具契约

前端工具页面不得维护工具参数表、工具 provider 表或返回字段表。前端必须从 `/api/tools` 获取工具契约，并按返回的 params、choices、return_fields、providers 渲染表单和结果。

### 4. 验证作为迁移护栏

验证应覆盖以下约束：
- 每个 `ToolSpec` 对应 MCP 工具函数，且必填参数可由 MCP 接收。
- MCP 函数体调用统一 ToolSpec dispatch helper，而不是手写 service target。
- CLI invoke 和 Dashboard invoke 对同一工具使用相同 service target 和参数归一逻辑。
- `/api/tools` 与 `ToolSpec` 投影一致。
- 前端页面不再维护独立工具参数表。

## Risks / Trade-offs

- [Risk] MCP 显式函数仍需要新增工具时补一个薄 wrapper，无法做到零代码暴露。  
  → Mitigation: validator 要求每个 ToolSpec 都有 MCP wrapper，并要求 wrapper 走统一 helper。

- [Risk] 统一 helper 改变已有 MCP 错误 JSON 或默认值处理。  
  → Mitigation: 先为 board、kline 等现有工具补 MCP 回归测试，再逐步迁移函数体。

- [Risk] CLI、Dashboard 的 provider 直调与 service 调用语义不同。  
  → Mitigation: provider 直调用于诊断，默认 invoke 走 service；测试中显式区分两类路径。

- [Risk] 前端看板可能仍有遗留硬编码。  
  → Mitigation: 增加静态检查或前端测试，验证工具表单来自 `/api/tools`。

## Migration Plan

1. 增加交付层统一 dispatch helper，复用 `ToolSpec` 的默认值、alias、service target 和 provider 信息。
2. 将 MCP 工具函数体逐步改为薄 wrapper，先迁移 board 相关函数，再覆盖其他已注册工具。
3. 让 CLI 和 Dashboard invoke 使用同一个 helper，保留现有命令和 HTTP API 兼容。
4. 增强 validators 和测试，覆盖 MCP/CLI/Dashboard/前端契约一致性。
5. 运行相关 pytest；前端变更后使用 Playwright 验证工具选择、表单渲染和调用结果。

回滚策略：保留显式 MCP 函数签名和现有 service 层不变；如果统一 helper 出现问题，可以临时将单个 wrapper 回退到原 service 调用，同时保留测试暴露差异。

## Open Questions

- 是否一次性迁移所有 MCP 函数，还是先迁移 board 及近期活跃工具后再分批完成。
- provider 直调的错误响应是否需要完全对齐 service 调用，还是明确标记为诊断模式。
