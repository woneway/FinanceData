# FinanceData 架构升级、落地、验证闭环方案

**日期**: 2026-04-09
**状态**: 已确认
**目标**: 建立一套适合大模型参与设计与实现的完整闭环，覆盖架构升级、实施落地、验证、发现问题后的修复再验证、直到最终交付。

---

## 1. 升级目标

本轮升级不是单纯新增几个接口，而是解决 FinanceData 在持续扩展后出现的几个根问题：

- CLI、MCP、dashboard、health、metadata 各自维护工具定义，系统真相分裂
- 新增接口和新增 provider 没有统一流程，容易出现断链和契约漂移
- 验证体系分散，无法回答“系统到底是否完成交付”
- 发现问题后缺少标准修复闭环，常出现“修了一个点，没有全局再验证”

本轮升级后的系统必须满足：

- 同时支持 `CLI + MCP` 两种正式交付能力
- 每个工具都能被健康检查、契约检查、真实冒烟检查覆盖
- 前后端消费同一套工具契约
- 新增接口和新增 provider 有统一模板和验收标准
- 最终交付结果由统一 `verify` 入口证明，而不是靠人工判断

---

## 2. 总体架构

升级后的架构分成 5 层：

```text
interface/     输入输出契约、Protocol、领域模型
provider/      单一数据源适配
service/       唯一业务入口，负责参数标准化、fallback、缓存、默认值
tool_specs/    统一工具注册中心，CLI/MCP/dashboard/health 共用
delivery/      对外交付层：cli / mcp / dashboard
```

依赖方向：

```text
delivery -> tool_specs -> service -> interface <- provider
```

原则：

- `provider` 不感知 CLI/MCP/dashboard
- `service` 是唯一业务真相层
- `tool_specs` 是唯一工具真相源
- `delivery` 只消费 `tool_specs + service`

---

## 3. 单一工具真相源

新增 `ToolSpec` 作为系统核心注册模型。

### 3.1 ToolSpec 负责描述

每个工具只在一处注册，至少包含：

- `name`
- `description`
- `domain`
- `input params`
- `return_fields`
- `service_target`
- `provider list`
- `freshness / history / cache`
- `probe config`
- `examples`

### 3.2 ToolSpec 消费方

以下模块全部从 `ToolSpec` 派生：

- MCP tool 暴露
- CLI 命令定义
- dashboard `/api/tools`
- health probe 参数
- consistency 检查配置
- registry consistency 校验

### 3.3 迁移原则

- 逐步删除 `_INVOKE_MAP`、`_TOOL_PROVIDERS`、前端硬编码参数表等平行配置
- `metadata/registry.py` 若保留，只做 `ToolSpec` 投影层，不再独立维护业务真相

---

## 4. CLI + MCP 双交付能力

FinanceData 对外正式支持两种能力：

### 4.1 MCP

定位：

- 供 AI Agent 以工具方式调用
- 对外暴露稳定工具集合
- 完全走 `service`

### 4.2 CLI

定位：

- 供开发者、调试、脚本、运维使用
- 成为 MCP 的可观测和可调试版本

建议命令：

- `finance-data tools`
- `finance-data describe <tool>`
- `finance-data invoke <tool> --json`
- `finance-data providers`
- `finance-data health [tool]`
- `finance-data verify`

### 4.3 统一要求

- CLI 和 MCP 使用同一套 `ToolSpec`
- CLI 和 MCP 输出结构尽量一致
- 所有外部调用最终都走 `service`

---

## 5. 健康检查体系

健康检查不是“有没有返回结果”，而是分层可定位。

### 5.1 三层健康检查

1. `provider health`
   检查网络、鉴权、可访问性、原始数据是否存在

2. `service health`
   检查参数标准化、fallback、缓存、默认值逻辑是否正确

3. `consistency health`
   检查多 provider 核心字段、记录数、单位的一致性

### 5.2 每个工具必须定义 ProbeSpec

ProbeSpec 至少包含：

- 默认探测参数
- 超时时间
- 最小记录数
- 关键字段
- 是否参与一致性检查

### 5.3 检查结果结构

健康检查结果统一返回：

- `tool`
- `provider`
- `status`
- `latency`
- `record_count`
- `error`
- `error_kind`
- `schema_ok`
- `unit_ok`

---

## 6. 前后端统一方案

前端不再硬编码工具参数，不再猜测表单结构。

### 6.1 后端统一暴露

`/api/tools` 至少返回：

- `name`
- `description`
- `domain`
- `params`
- `return_fields`
- `providers`
- `freshness`
- `supports_history`
- `examples`

### 6.2 前端职责

前端只负责：

- 根据 `params` 渲染表单
- 根据 `return_fields` 和返回数据渲染结果
- 根据 health API 渲染状态

### 6.3 契约要求

- frontend 表单参数必须来自后端契约
- frontend 不能再维护独立工具参数表
- dashboard invoke / health / tool detail 全部基于同一数据源

---

## 7. 新增接口和新增 provider 的标准流程

### 7.1 新增接口

固定流程：

1. 在 `interface/<domain>/` 定义输入输出模型与 protocol
2. 在 `provider/<source>/<domain>/` 实现单源适配
3. 在 `service/<domain>.py` 接入 dispatcher/fallback/cache
4. 在 `tool_specs/registry.py` 注册工具
5. 自动获得 CLI/MCP/dashboard 能力
6. 补验证

必须补的验证：

- provider 单元测试
- service 测试
- ToolSpec consistency 测试
- MCP 调用测试
- CLI 调用测试
- 必要时加真实 smoke

### 7.2 新增 provider

固定流程：

1. 实现 provider，满足对应 protocol
2. 统一字段、单位、错误类型
3. 在 service 中接入 provider 优先级
4. 补 consistency 检查
5. 补 provider 与 service 测试
6. 加入 provider health 检查

---

## 8. 验证体系

验证必须形成固定金字塔，不依赖人工主观判断。

### 8.1 静态一致性验证

检查系统定义是否自洽：

- 所有 `tool_*` 都在 `ToolSpec`
- `ToolSpec.service_target` 存在
- MCP / CLI / dashboard 参数定义一致
- probe 参数可以通过签名校验
- metadata 与 ToolSpec 一致

### 8.2 单元验证

覆盖：

- provider 字段映射
- 单位转换
- 错误归类
- service fallback
- service 参数标准化
- cache/defaults

### 8.3 集成验证

覆盖：

- MCP 调 service
- CLI 调 service
- dashboard invoke
- health probe

### 8.4 真实冒烟

覆盖：

- 核心工具真实调用
- provider 可达性
- 基础延迟
- 最小数据返回

### 8.5 跨源一致性验证

适用于多 provider 工具：

- 记录数
- 主键匹配
- 关键字段一致性
- 单位一致性
- 缺失字段差异

---

## 9. 统一 verify 入口

最终所有完成状态由一条命令证明：

```bash
uv run python -m finance_data.verify
```

`verify` 负责执行：

- registry consistency check
- schema / signature check
- provider / service unit tests
- CLI / MCP / dashboard integration tests
- selected smoke tests
- health / consistency sanity checks

原则：

- `verify` 不通过，不算完成
- 大模型不能只汇报“已实现”，必须给出 `verify` 结果

---

## 10. 发现问题后的修复再验证闭环

每个问题进入统一状态机：

1. `发现`
2. `归类`
3. `定位`
4. `修复根因`
5. `补回归测试`
6. `局部验证`
7. `全局 verify`
8. `记录并关闭`

### 10.1 问题归类

统一归类为：

- ToolSpec 契约问题
- service 逻辑问题
- provider 实现问题
- MCP 交付层问题
- CLI 交付层问题
- dashboard 展示问题
- 外部环境问题

### 10.2 修复原则

- 不修表象，必须修根因层
- 每个 bug 修复必须带一个新测试
- 修复后先跑受影响测试，再跑全局 verify

### 10.3 关闭标准

问题只有在以下条件满足后才能关闭：

- 根因已修复
- 回归测试已新增
- 局部验证通过
- 全局 verify 通过

---

## 11. 分阶段实施计划

### 阶段 1：统一真相源

目标：

- 引入 `ToolSpec`
- MCP、dashboard、health 从 ToolSpec 派生
- 移除重复工具配置

验收：

- 同一工具不再多处手写定义
- `/api/tools`、MCP、health 一致

### 阶段 2：CLI 落地

目标：

- 增加正式 CLI 能力
- CLI 全部走 service

验收：

- 可以枚举、描述、调用、健康检查

### 阶段 3：健康检查升级

目标：

- provider health / service health / consistency health 分层
- dashboard 和 CLI 共用 probe engine

验收：

- 每个工具可探测
- 失败结果可定位

### 阶段 4：verify 体系落地

目标：

- 一条命令收敛所有关键验证

验收：

- 本地可复现
- 可接入 CI

### 阶段 5：开发与交付规范固化

目标：

- 固定新增接口 / provider 模板
- 固定交付报告格式

验收：

- 新成员能按文档扩展系统

---

## 12. 最终交付标准

最终交付不是“代码 merge”，而是同时满足：

- CLI 可用
- MCP 可用
- dashboard 可用
- 核心工具 health 可用
- verify 通过
- 新增接口和 provider 有标准开发流程
- 文档可指导后续扩展和运维

最终交付包至少包含：

- 架构说明
- 能力清单
- 验证报告
- 运维说明
- 开发说明

---

## 13. 下一步执行顺序

建议严格按以下顺序推进：

1. `ToolSpec` 注册中心
2. CLI 交付层
3. 健康检查统一引擎
4. verify 总入口
5. 开发规范和交付文档

不要跳步。先解决系统真相分裂，再扩 CLI/MCP/health/verify，后续成本最低。
