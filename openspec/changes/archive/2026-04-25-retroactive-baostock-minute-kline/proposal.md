# RETROACTIVE — 历史合规化 change

> 本 change 为 ab32a22（2026-04-20，feat: 新增分钟K线接口）的 retroactive 制品，仅用于补齐 OpenSpec 合规材料，不修改任何代码。代码已在 ab32a22 + c010fe9（2026-04-25 baostock 依赖锁定）合入主干。

## Why

ab32a22 commit 在 OpenSpec 流程外引入了一个新的金融数据领域能力：分钟级 K 线（5/15/30/60min），数据源 baostock。该接入：

- 是 FinanceData 第一个 baostock provider，且 baostock 此前是孤立安装、未在 `pyproject.toml` 声明（c010fe9 才补救），违反「新数据源接入必须先做上游对齐」的项目纪律。
- 引入了「免费但有上游政策风险」的数据源（baostock 0.9.1 已迁服务地址，旧版直接登录超时），需要在 spec / docs 中显式声明权限敏感性。
- 未走 propose / spec / upstream-alignment / acceptance 流程，使后续维护者无法从 OpenSpec 历史定位其设计意图。

阶段 1 的 `kline-history` capability 已为分钟 K 线预留 7 条 Requirement（含「分钟无 fallback」「分钟权限敏感性」「东财绕代理不适用」等）。本 retroactive change 补齐：合规材料 + 上游对齐文档 + 验收记录，让 ab32a22 与 c010fe9 在 OpenSpec 历史中有迹可循。

## What Changes

- 新增 `openspec/changes/archive/2026-04-25-retroactive-baostock-minute-kline/` 历史合规归档：proposal / design / tasks / acceptance / upstream-alignment。
- 不在 `kline-history` capability 上做任何 ADDED / MODIFIED / REMOVED；该 capability 在阶段 1 已覆盖分钟 K 线相关 Requirement。
- 不修改任何 src/ 代码、不修改 pyproject.toml、不修改 config.toml。
- 非目标：不重新评估是否引入 baostock，不改变 baostock 的 fallback 策略，不调整分钟 K 线的工具签名。
- 兼容性：纯文档动作，运行时零影响。
- 上线风险：无。

## Capabilities

### Modified Capabilities
- 无（`kline-history` 已在阶段 1 包含分钟 K 线全部 Requirement，本 change 仅做合规追认）。

### New Capabilities
- 无。

### Removed Capabilities
- 无。

## Impact

- 受影响代码：无。
- 受影响 spec：无。
- 历史 commit 追溯：ab32a22（2026-04-20，feat 主体）+ c010fe9（2026-04-25，pyproject.toml 锁定 baostock>=0.9.1）。
- 依赖：复用 `kline-history` capability 已定义的 Requirement；复用阶段 0 落地的 `openspec/templates/` 两份模板。
