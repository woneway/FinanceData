## 1. 统一交付层 dispatch 基础

- [x] 1.1 新增交付层共享 dispatch helper，按工具契约应用默认值、alias 归一、service target 调用，并验证“业务调用统一进入 service / 默认调用路径”。
- [x] 1.2 支持显式 provider 诊断调用，仅允许调用工具契约声明的 provider，并验证“provider 诊断调用”。
- [x] 1.3 为 helper 增加单元测试，覆盖未知工具、缺失 service target、必填参数缺失、provider 未注册、调用异常 JSON 化。

## 2. MCP 收敛到工具契约

- [x] 2.1 将 board MCP 工具函数体改为薄 wrapper，经统一 helper 调用 service，并验证“MCP wrapper 调用已注册工具”。
- [x] 2.2 分批迁移其余已注册 MCP 工具函数体，保持函数名、签名和 docstring 兼容，并验证“MCP 工具契约不得漂移”。
- [x] 2.3 强化 MCP validator，检查每个可交付工具存在 MCP 暴露、必填参数可被接收、wrapper 未绕过统一 helper，并验证“MCP 缺少工具 / MCP 参数不匹配”。
- [x] 2.4 更新 MCP 回归测试，覆盖默认值、trade_date/start_date/end_date、错误 JSON 和 service mock 调用参数。

## 3. CLI 与 Dashboard API 复用同一调用逻辑

- [x] 3.1 将 CLI invoke 的 service 调用和 provider 诊断调用切换到共享 helper，并验证“调用路径校验”。
- [x] 3.2 将 Dashboard `/api/tools/{tool}` invoke 切换到共享 helper，保持响应结构和 metrics 记录兼容。
- [x] 3.3 更新 CLI 与 Dashboard API 测试，覆盖同一工具在两个入口下使用一致参数归一和 service target。

## 4. 前端看板契约校验

- [x] 4.1 检查并移除前端工具调用页面中的本地工具参数、provider、返回字段硬编码，验证“前端看板不得维护独立工具表”。
- [x] 4.2 增加前端或端到端测试，覆盖 `/api/tools` 加载、动态参数表单渲染、choices 展示和调用请求参数。
- [x] 4.3 使用 Playwright 验证工具选择、参数输入、调用反馈和结果表格渲染。

## 5. 验证闭环与文档

- [x] 5.1 更新 `finance-data verify --include-dashboard` 或相关 validators，使其覆盖注册表、MCP、Dashboard API 和前端契约一致性。
- [x] 5.2 运行后端相关 pytest：tool_specs、MCP、CLI、Dashboard API 测试，并记录未覆盖场景。
- [x] 5.3 更新开发文档或 README，说明新增工具时必须先注册 ToolSpec，再补 MCP wrapper 和交付层验证。
- [x] 5.4 完成最终验收，按 Completeness、Correctness、Coherence 记录结论、spec drift、未测试项和上线风险。
