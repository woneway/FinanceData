## Context

本 change 是对 ab32a22（2026-04-20）+ c010fe9（2026-04-25）的 retroactive 合规。两个 commit 共同完成了「分钟 K 线 baostock 接入」能力，但当时未走 OpenSpec：

- ab32a22 引入 5/15/30/60min 分钟 K 线接口、`baostock` 第一个 provider、新 `interface/kline/minute.py`、`service/kline.py` 加 `_MinuteKlineDispatcher`、`tool_specs/registry.py` 加 `tool_get_kline_minute_history`、`client.py` 加 `fd.kline_minute()`。
- c010fe9 暴露：baostock 此前是孤立安装、未在 `pyproject.toml` 声明，0.9.1 之后服务器迁移导致旧版不可用。

阶段 1 的 `kline-history` capability 已基于这两个 commit 反推，预留了「分钟无 fallback」「分钟权限敏感性」相关 Requirement。本 change 在此基础上：
- 用 MODIFIED 强化「权限敏感性」Requirement，融入 baostock>=0.9.1 的硬约束。
- 用 `upstream-alignment.md` 沉淀 baostock 调用细节（接口签名、字段、单位、复权映射、代码格式转换）。
- 用 acceptance.md 记录验收过程与已通过测试。

source-of-truth 映射：

| 层级 | Source of truth | 本 change 操作 |
| --- | --- | --- |
| spec capability | `kline-history`（阶段 1 落地） | MODIFIED 1 条 Requirement |
| 历史 commit | ab32a22 + c010fe9 | 引用，不修改 |
| 实际接入代码 | `provider/baostock/kline/minute.py`、`service/kline.py`、`tool_specs/registry.py`、`client.py`、`interface/kline/minute.py` | 不修改 |
| 依赖声明 | `pyproject.toml` baostock>=0.9.1 | 不修改（已由 c010fe9 落地） |

## Goals / Non-Goals

**Goals:**
- 把 ab32a22 + c010fe9 的设计意图、实施过程、上游对齐结论沉淀到 OpenSpec，为后续维护者提供可追溯的合规材料。
- 用 MODIFIED 的方式强化 `kline-history` 中分钟相关 Requirement，融入 c010fe9 揭露的 baostock 版本约束。
- 不重新评估技术决策（baostock 是否合适、是否应加 fallback 等），仅追认现状。

**Non-Goals:**
- 不修改任何 src/ 代码、不修改 pyproject.toml、不修改 config.toml。
- 不调整 `tool_get_kline_minute_history` 的工具签名（含参数 / 返回字段 / docstring）。
- 不补 fallback provider（tushare 分钟权限未启用，本 change 不动）。
- 不评估 baostock 的长期可用性（外部依赖风险，本 change 仅记录事实）。

## Decisions

### 1. 用 MODIFIED 而非 ADDED 强化分钟权限敏感性 Requirement

**理由**：
- 阶段 1 的 `kline-history` 已有「分钟 K 线必须显式声明权限敏感性」Requirement，描述了「免费源策略 + tushare 权限策略」两类风险。
- 本 retroactive 在实施过程中发现的新约束（baostock>=0.9.1）属于同一 Requirement 的细化，应 MODIFIED 而非 ADDED 新 Requirement。
- MODIFIED 保留原 Requirement 名称的同时扩展约束内容，不破坏 `kline-history` 的结构。
- OpenSpec MODIFIED 必须包含完整 Requirement 内容（含全部 Scenario），本 change 在原 1 个 Scenario 基础上扩展为 3 个 Scenario（权限提示 + 依赖最低版本 + 服务地址变更容错）。

### 2. retroactive 不重写已实施的代码

**理由**：
- ab32a22 + c010fe9 已在主干稳定运行（405 tests passed），且阶段 1 的 spec 是基于实际行为反推。
- retroactive 的核心价值是「补合规材料」，而非「质疑过往实现」。
- 任何想要修改实施的动机应单独走新 change，不混入 retroactive。

### 3. upstream-alignment 用反推方式产出

**理由**：
- 实施时未做 upstream-alignment，本 change 用模板将 baostock 上游接口的字段、单位、参数语义记录下来。
- 信息源：`provider/baostock/kline/minute.py` 的代码事实 + ab32a22 commit message + c010fe9 commit message。
- 这与「正向流程的 upstream-alignment（先做对齐再写代码）」相比，缺少「真实调用 + 打印 columns」的现场证据，但作为合规追认材料已够用；后续若需要更高质量的对齐，可独立 change 触发 baostock provider 全面回归测试。

## Source-of-Truth 映射（实施 → spec）

| 实施事实 | 来源 | 对应 Requirement / Scenario |
| --- | --- | --- |
| 5/15/30/60min 四档 period | `_VALID_PERIODS` in `provider/baostock/kline/minute.py` | kline-history「按周期独立暴露」覆盖 |
| 单源无 fallback | `_build_minute()` in `service/kline.py` | kline-history「默认主源 fallback」分钟无 fallback Scenario |
| volume/amount 无需换算 | provider 代码无 `_safe_float() *` 操作 | upstream-alignment 字段映射表 |
| 复权映射 qfq=2/hfq=1/none=3 | `_ADJ_MAP` | upstream-alignment 字段映射表 |
| baostock>=0.9.1 锁定 | `pyproject.toml`（c010fe9） | 本 change MODIFIED 新增 Scenario |
| 服务地址迁移导致旧版不可用 | c010fe9 commit message | 本 change MODIFIED 新增 Scenario「服务地址变更后的容错」 |

## Risks / Trade-offs

- [Risk] retroactive 的 spec MODIFIED 比当前实现更严格（要求 DataFetchError 携带 baostock 版本与服务地址提示）。  
  → Mitigation: 当前实现仅抛 baostock 原始错误信息，未显式带版本号。这构成 spec drift。处理：在 acceptance.md 中显式记录该 drift，并标记为「待跟进」（不在本 retroactive 中修代码，留给独立后续 change）。

- [Risk] tushare 分钟接口（`stk_mins`）未来权限放开后，是否应作为 baostock fallback？  
  → Mitigation: 不在本 retroactive 中决策，留作 backlog。

- [Risk] retroactive 的 upstream-alignment 缺现场证据（未真实调用接口验证 columns）。  
  → Mitigation: 已通过代码事实推导；若日后发现字段差异，触发独立的「baostock provider 验收」change。

## Migration Plan

1. 创建 `proposal.md`、`design.md`、`tasks.md`、`upstream-alignment.md`、`acceptance.md` 五份制品。
2. 在 `specs/kline-history/spec.md` 写 MODIFIED Requirement，扩展为 3 个 Scenario。
3. `openspec validate retroactive-baostock-minute-kline --strict` 通过。
4. 写 acceptance.md，记录 spec drift（实现未带版本号到 DataFetchError）。
5. `openspec archive retroactive-baostock-minute-kline`，把 `kline-history` 中对应 Requirement 替换为 MODIFIED 版本。

回滚策略：纯文档动作，回滚为 `git revert` 即可。

## Open Questions

- spec drift「实现未带版本号到 DataFetchError」：是立即修代码、还是开独立 change 跟进？  
  → 倾向于独立 change，因为本 retroactive 的纪律是「不修代码」。drift 在 acceptance.md 中标记，进 backlog。
