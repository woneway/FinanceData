## Context

`openspec/specs/` 当前有三份 K 线 capability：daily-kline-history、weekly-kline-history、monthly-kline-history。Explore 阶段用 `diff` 验证三份 95% 文本相同（仅替换「日 / 周 / 月」字样与少量 Scenario 名）。这违反 SDD 原则「外部行为不变就不该写多份 spec」。

合并理由：
- 三份 spec 的核心 4 条 Requirement（独立能力 / 上游对齐 / 默认 provider 链 / 后台可观测）本质是同一组行为契约的 period 复制。
- 周 / 月独有「每日更新语义 + 未完成周期处理」与日独有「Web 后台展示状态」、月独有「前端独立入口」散落在三份文件中，跨文件维护成本高。
- 阶段 2 即将接入分钟 K 线 spec，按现有模式会变成 4 份近乎重复 spec。

本 change 仅做 spec 层收敛，不动任何 src/ 代码。

source-of-truth 映射：

| 层级 | Source of truth | 本 change 操作 |
| --- | --- | --- |
| spec capability | `openspec/specs/kline-history/` | 新增 |
| 旧 spec capability | `openspec/specs/{daily,weekly,monthly}-kline-history/` | 删除（archive 时由 OpenSpec REMOVED 自动处理） |
| 上游对齐依据 | `archive/2026-04-10-split-kline-history-by-period/upstream-alignment.md` | 引用，不修改 |
| 实现层 | service/kline.py、provider/{tushare,akshare,baostock}/kline/ | 不修改 |

## Goals / Non-Goals

**Goals:**
- 单一 `kline-history` spec 覆盖 daily / weekly / monthly / minute 四个周期。
- 通用约束（独立暴露、上游对齐、默认 provider 链、后台可观测）按周期参数化，一处定义。
- 周期专属约束（每日更新语义、未完成周期处理、分钟权限敏感）显式且可独立验证。
- 阶段 2 接入分钟 K 线时，无需新增 spec capability，仅在 `retroactive-baostock-minute-kline` 中按 ADDED Requirements 增量挂入 `kline-history`（实际上本 change 已在新 spec 中预留分钟相关 Requirement，阶段 2 只需补 retroactive 历史依据）。

**Non-Goals:**
- 不修改任何 src/ 代码，不修改任何 provider/service/MCP/CLI/Dashboard 行为。
- 不改变 MCP 工具名（仍是 `tool_get_kline_daily_history` 等四个独立工具）。
- 不修改 `delivery-tool-spec-contract`、`openspec-governance` 等其他 capability。
- 不引入新的周期类型（如年线、季线）。

## Decisions

### 1. 选择「合并到一个 capability」而非「保留三个 + 共享文档」

**选项**：
- A. 三份 spec 不动，只在 README 或交叉引用中说明它们共享行为。
- B. 合并为单一 `kline-history` capability，按周期参数化。

**选择 B**。

**理由**：
- A 维持 spec drift 风险，任何一处更新都要同步三份。
- B 让 spec 真正是「行为契约」而非「实现切片」，符合 wiki `[[spec-driven-development]]` 「外部行为不变就不该写多份 spec」原则。
- B 让分钟 K 线在阶段 2 自然挂入，无需新建 capability。

### 2. 周期专属 Scenario 通过「分 Scenario」而非「分 Requirement」表达

**理由**：
- 每个 Requirement 描述一类约束，多个 Scenario 描述该约束在不同周期下的具体行为。
- 例如「未完成周期处理」是一个 Requirement，包含「日线时效」「周/月未完成周期一致性」「分钟实时未完成 bar」三个 Scenario。
- 这避免了「日线独立暴露 / 周线独立暴露 / 月线独立暴露」式的重复 Requirement。

### 3. 「东财 fallback 必须配置代理绕过」单独成 Requirement

**理由**：
- 该约束跨周期（仅周 / 月线 fallback 触及，但是 implementation-aware 的强约束）。
- 单独成 Requirement 让阶段 3 `cleanup-config-and-proxy-leftovers` 的守护测试有明确 spec 依据。
- 不写成 Scenario 是因为它是「跨多个 Scenario 都成立的强约束」而非「在某个 WHEN 下的行为」。

### 4. 分钟 K 线相关 Requirement 在本 change 一次性定义

**选项**：
- A. 本 change 只合并日 / 周 / 月，分钟 K 线留给阶段 2 retroactive change ADDED。
- B. 本 change 一次性定义包含分钟 K 线在内的统一 spec，阶段 2 仅补 retroactive 历史依据（proposal/upstream-alignment/tasks）但不再修改 spec。

**选择 B**。

**理由**：
- A 会让阶段 2 的 retroactive change 还要做 spec ADDED，复杂度增加。
- B 让 spec 一次到位，阶段 2 只回填历史合规材料，更干净。
- 风险：阶段 2 实施时可能发现分钟 K 线的实际行为与本 change 写的 Requirement 不一致 → 触发 spec drift 流程，按 governance 要求先同步 spec 再继续，可控。

### 5. 旧三份 capability 在本 change 不走 REMOVED，archive 后手动 rm -rf

**背景**：实际归档时发现 OpenSpec 1.2.0 拒绝产生「全部 Requirement 被 REMOVED」的空 spec，校验器报「Spec must have at least one requirement」并 abort。

**选项**：
- A. 在本 change 中保留 REMOVED 段，强行通过 `--no-validate` 归档（不推荐，污染历史 spec）。
- B. 本 change 仅 ADDED 新 kline-history，archive 完成后由维护方手动 `rm -rf openspec/specs/{daily,weekly,monthly}-kline-history/`。
- C. 拆分为多个 change，逐个废弃旧 capability（成本高，本 change 收敛初衷为消除重复）。

**选择 B**。

**理由**：
- A 用 `--no-validate` 会让所有人忽略 strict 校验，破坏阶段 0 治理立的口径。
- B 让 OpenSpec 的 ADDED 流程保持纯净，capability 删除走「不可逆物理操作」单独决策。
- C 与本 change 一次性合并的目标冲突。
- 副作用：归档后必须立即执行手动清理（写入 tasks 4.2），否则三份旧 spec 与新 spec 共存导致语义双重定义。
- design 中保留 source-of-truth 映射表 + acceptance.md 的 Migration 记录，作为旧 spec 行为已迁移的审计证据。

## Source-of-Truth 映射

| Requirement（new kline-history） | 迁移自（old spec）| Migration 完整度 |
| --- | --- | --- |
| 个股历史 K 线必须按周期独立暴露 | daily/weekly/monthly 各自的「独立能力对外提供」 | 4 个 Scenario 覆盖 CLI/MCP/HTTP/前端 |
| 个股历史 K 线必须先完成上游对齐再实现 provider | 三份的「上游对齐」Requirement | 增强为 7 维度上游对齐 + 阻断 archive |
| 各周期 K 线必须显式定义更新时效与未完成周期处理 | weekly/monthly 的「每日更新语义」 + 新增分钟 / 日线时效 | 跨四周期 |
| 各周期 K 线必须采用项目偏好的默认主源与 fallback | daily/weekly 的「默认主源 fallback」 | 显式列出四周期默认链 |
| 涉及东财上游的周期 K 线 fallback 必须配置代理绕过 | 来自项目代码事实（akshare/_proxy.py），原 spec 未显式 | 新增显式约束 |
| 各周期 K 线必须在 Web 管理后台暴露源级状态 | daily 的「Web 管理后台展示」 | 扩展为四周期 |
| 分钟 K 线必须显式声明权限敏感性 | 来自实际接入 baostock/tushare 分钟权限事实，原 spec 无 | 新增 |

## Risks / Trade-offs

- [Risk] 合并时遗漏周期专属 Scenario。  
  → Mitigation: design.md 上方 source-of-truth 映射表逐条对照旧三份 Requirement，REMOVED 中显式给出 Migration。Verify 阶段做最终核对。

- [Risk] 阶段 2 分钟 K 线接入后发现 spec 中分钟相关 Requirement 与实际不符。  
  → Mitigation: 按 `openspec-governance` 的 apply 规则「drift 时先同步 spec 再继续」处理。本 change 的分钟相关 Requirement 已基于 ab32a22 commit 的实际实现（baostock 5/15/30/60min，无 fallback）撰写。

- [Risk] 旧三份 spec 的物理目录在 archive 后留空。  
  → Mitigation: tasks 中包含「archive 后手动 `rm -rf` 空目录」步骤，由维护方执行。

- [Risk] historical archive 中的 spec delta 文件（archive/2026-04-10/specs/{daily,weekly,monthly}-kline-history/）在 capability 删除后变成「指向不存在 capability 的历史记录」。  
  → Mitigation: 保留不动，作为历史归档记录。OpenSpec 不要求 historical archive 与当前 specs/ 一致。

## Migration Plan

1. 创建 `openspec/changes/consolidate-kline-history-specs/specs/kline-history/spec.md`，写 ADDED Requirements（7 条）。
2. 在 acceptance.md 中显式记录旧三份 capability 的 12 条 Requirement 与新 spec 7 条 Requirement 的等价覆盖关系（替代 OpenSpec REMOVED 机制提供的审计追踪，因 OpenSpec 不允许空 capability）。
3. `openspec validate --strict` 确认 spec delta 自身合法。
4. 本地预演：`openspec show consolidate-kline-history-specs --type change --json` 输出含 kline-history ADDED 7。
5. 写 acceptance.md，逐 Requirement 核对 Migration 是否完整覆盖。
6. `openspec archive consolidate-kline-history-specs`，OpenSpec 仅新增 `specs/kline-history/spec.md`，不动旧三份。
7. archive 后**立即**手动清理三份旧 capability 目录：`rm -rf openspec/specs/{daily,weekly,monthly}-kline-history/`。此步骤是本 change 不可缺的物理清理，未做则视为本 change 未完成。
8. 运行 `openspec list --specs` 确认最终 capability 列表。

回滚策略：本 change 仅动 spec markdown，回滚为 `git revert` + 重建 `openspec/specs/{daily,weekly,monthly}-kline-history/spec.md`，运行时零影响。

## Open Questions

- 阶段 2 retroactive change `retroactive-baostock-minute-kline` 是否需要在 spec 上做任何 ADDED？  
  → 本 change 已预留分钟相关 Requirement，预期阶段 2 仅回填 proposal/upstream-alignment/tasks/acceptance，spec 段无需新增。若阶段 2 发现实际行为与本 spec 偏差，触发 drift 流程。
- 是否要保留三份旧 capability 目录作为「历史路标」（空目录 + 一个 README 指向 kline-history）？  
  → 暂不保留，git history 已是历史记录。空目录直接删。
