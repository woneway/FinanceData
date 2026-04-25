# RETROACTIVE — 任务清单

> 本 change 是历史合规追认，所有「实现」步骤已在 1e0ae0b 完成。任务清单仅追溯实施时该做但未做的合规材料。

## 1. 起草 retroactive 制品

- [x] 1.1 创建 `proposal.md`，记录本 change 是 retroactive、覆盖 1e0ae0b commit、明确把「配置统一 / 大规模死代码清理 / 治理空白」三类变更分开声明。
- [x] 1.2 创建 `design.md`，含 source-of-truth 映射表（8 行）+ 5 条 Decision（仅沉淀 A 类 / 显式追踪 os.environ 残余 / 装配阶段降级 / 不规定 TOML 字段名 / volume_ratio 不进本 capability）。
- [x] 1.3 不需要 upstream-alignment.md（本 change 不接入新数据源）。

## 2. 起草新 capability spec

- [x] 2.1 在 `specs/configuration/spec.md` 写 6 条 ADDED Requirements：唯一事实来源 / 不入 git / helper 函数封装 / 缺省语义 / token 缺失降级 / 缺失文件错误信息。
- [x] 2.2 `openspec validate retroactive-config-toml-consolidation --strict` 通过。

## 3. 写 acceptance 并归档

- [x] 3.1 写 `acceptance.md`，按 Completeness / Correctness / Coherence + 三类风险显式记录。Spec Drift 段已显式记录两项残余 `os.environ.get` 并标注「待阶段 3 清理」。
- [ ] 3.2 `openspec archive retroactive-config-toml-consolidation -y`，自动新增 `specs/configuration/spec.md`。验证：`openspec list --specs` 显示 8 个 capability（原 7 + 新 1）。
- [x] 3.3 不需要任何代码或目录清理（本 change 不动 src）。
