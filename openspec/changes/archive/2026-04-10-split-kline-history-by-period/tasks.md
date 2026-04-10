## 实施任务

- [x] 1. 完成日线、周线、月线的上游对齐记录
  - 为 `tushare` 与 `akshare` 分别定位官方文档入口
  - 实际调用原始接口，确认字段、单位、更新时间和未完成周期语义
  - 将对齐结论写回本 change 的 design 或补充说明

- [x] 2. 改造 provider 层
  - 拆分或重组历史 K 线 provider，使日线、周线、月线分别适配
  - 默认只启用 `tushare` 和 `akshare`
  - 关闭其它源在新历史 K 线主交付链中的默认参与

- [x] 3. 改造 service 层
  - 建立独立的日线、周线、月线 dispatcher
  - 统一各自对外语义
  - 明确主源和 fallback 行为

- [x] 4. 改造 ToolSpec、CLI、MCP 和 HTTP API
  - 新增三个独立工具定义
  - 删除旧历史 K 线工具中的周期驱动入口
  - 确保 CLI、MCP、HTTP API 使用新契约

- [x] 5. 改造前端页面和管理后台
  - 前端调用页面改为三个独立历史 K 线入口
  - 移除股票历史 K 线周期下拉
  - 后台保留 provider 健康度、service 状态和验收视图

- [x] 6. 更新测试与验收
  - 更新 provider、service、CLI、MCP、HTTP API 和前端页面相关测试
  - 使用 Playwright 验证前端真实调用与渲染
  - 形成日线、周线、月线三个独立接口的验收结论

- [x] 7. 更新文档与迁移说明
  - 更新相关开发文档、接口说明和后台说明
  - 明确旧 `tool_get_kline_history` 下线和新接口迁移方式
