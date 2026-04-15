## 验收结论

变更 `unify-delivery-tool-specs` 已完成实现和验证。CLI、MCP、Dashboard API 和前端看板已统一消费 `ToolSpec` 工具契约，默认业务调用最终进入 service。MCP 保留显式函数签名，函数体通过统一 ToolSpec dispatch helper 调用注册工具。

## Completeness

- 已新增交付层共享 dispatch helper，覆盖 service 调用、provider 诊断调用、参数默认值、alias 归一和必填参数校验。
- 已迁移所有已注册 MCP 工具函数体到统一 helper。
- 已将 CLI invoke 和 Dashboard invoke 切换到共享 helper。
- 已移除前端工具调用页和健康页中的本地工具/参数契约表。
- 已更新 README 中新增工具流程。

## Correctness

已执行并通过：

- `uv run pytest tests/tool_specs/test_invoke.py`
- `uv run pytest tests/mcp/test_mcp_error_handling.py tests/mcp/test_mcp_default_dates.py`
- `uv run pytest tests/tool_specs/test_registry_consistency.py`
- `uv run pytest tests/cli/test_cli.py tests/dashboard/test_api.py tests/provider/metadata/test_validator_toolspec_alignment.py`
- `uv run pytest tests/test_verify.py tests/tool_specs/test_registry_consistency.py`
- `uv run pytest tests/tool_specs tests/mcp tests/cli/test_cli.py tests/dashboard/test_api.py tests/provider/metadata/test_validator_toolspec_alignment.py tests/test_verify.py`
- `uv run finance-data verify --include-dashboard --json`
- `cd frontend && npm run build`

Playwright 已验证：

- Dashboard 页面加载 `/api/tools` 后显示 44 个工具。
- 工具调用页可搜索并选择 `tool_get_board_member_history`。
- 参数表单由后端契约动态渲染，`idx_type` choices 可见。
- 输入 `board_name=银行`、`trade_date=20260414` 后调用成功并渲染结果表格。

## Coherence

- `ToolSpec` 继续作为工具契约真相源。
- service 继续作为业务语义真相层。
- provider 直调仅保留为诊断路径，默认调用路径不绕过 service。
- `FinanceData` Python 客户端未纳入本次收敛，保持领域 API 直接调用 service。

## 未测试项与风险

- 未运行全量 provider 真实数据测试；本 change 不修改 provider 数据语义。
- 前端 Playwright 验收覆盖了一个代表性工具，未逐一点击全部 44 个工具。
- `frontend build` 会刷新 dashboard static 产物，提交时需要确保静态产物和源码变更保持一致。

## Spec Drift

未发现 proposal、design、spec 与实现不一致项。
