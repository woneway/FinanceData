<!-- 用 openspec/templates/acceptance.template.md 落地。 -->
<!-- 本 change 是 retroactive，「实现」由 1e0ae0b 完成；本验收聚焦合规材料完整性 + 残余 os.environ.get 的 drift 显式记录。 -->

## 验收结论

变更 `retroactive-config-toml-consolidation` 已完成 retroactive 合规追认。1e0ae0b（2026-04-19）的「配置统一 + 大规模死代码清理」refactor 已沉淀为 OpenSpec 可追溯材料：proposal / design / tasks / acceptance 四份制品齐全。新建 `configuration` capability 含 6 条 Requirement，覆盖项目级配置统一规范。本 change 不修改任何 src/ 代码。识别 1 项 spec drift（残余 `os.environ.get` 读取）已显式记录并指向阶段 3 清理。

## Completeness

- 已落地 retroactive proposal：顶部标注 RETROACTIVE，说明 1e0ae0b 携带三类变更（A 配置统一 / B 死代码清理 / C 治理空白），明确仅 A 类沉淀为 capability。
- 已落地 retroactive design：含 source-of-truth 映射表（8 行）+ 5 条 Decision + 风险段（含残余 os.environ 预警）。
- 已落地新 capability `configuration`：6 条 ADDED Requirement，覆盖唯一事实来源 / 不入 git / helper 函数封装 / 缺省语义 / token 缺失降级 / 缺失文件错误信息，含 10 个 Scenario。
- 历史合规追认覆盖：1e0ae0b 涉及的 70 个文件中，A 类（配置统一）的核心文件 `src/finance_data/config.py` + service 层降级逻辑均在 source-of-truth 映射中可定位；B 类（死代码清理）作为已发生事实在 design.md「Context」段记录，不进入 spec；C 类（治理空白）由阶段 0 governance 元约束承接。

## Correctness

已执行并通过：

- `openspec validate retroactive-config-toml-consolidation --strict` → `Change 'retroactive-config-toml-consolidation' is valid`
- `git show --stat 1e0ae0b` → 确认涉及 70 个文件、325 行新增、1816 行删除
- `cat src/finance_data/config.py` → 确认 helper 函数实现：`@lru_cache(maxsize=1)` _load + 5 个 helper（get_tushare_token / get_tushare_api_url / get_xueqiu_cookie / has_tushare_token / has_tushare_stock_minute_permission）
- `grep "config.toml" .gitignore` → 确认 .gitignore 排除 config.toml
- `ls config.toml.example` → 确认模板文件存在
- `grep -rn "os.environ.get" src/finance_data/` → 确认仅 2 处残余（cache/resolver.py:41 的 FINANCE_DATA_CACHE、provider/akshare/_proxy.py:13,16 的 no_proxy），与 design.md 风险段一致
- 历史回归：1e0ae0b commit message 声明「400 passed, 0 failed」，本 change 不动代码，无需重跑测试

## Coherence

- 仅沉淀 A 类（配置统一）为 capability；B 类（死代码清理）和 C 类（治理空白）按 design.md Decision 1 分别处理为「事实记录」和「元约束承接」。
- `configuration` Requirement「残余环境变量读取必须显式追踪」明确不在本 change 修代码（与 retroactive 纪律一致），仅要求「必须开 OpenSpec change 迁移」（与 design.md Decision 2 一致）。
- spec 不规定具体 `[tushare]` / `[xueqiu]` TOML 字段名，由 `config.toml.example` 与 `config.py` helper 共同决定（与 design.md Decision 4 一致）。
- token 缺失时的「装配阶段降级」明确写为 Requirement，避免未来误改成「调用阶段抛错」（与 design.md Decision 3 一致）。
- `daily_basic.volume_ratio` fallback 不进入 `configuration` capability，留作 backlog（与 design.md Decision 5 一致）。

## 未测试项与风险

- **未实测「config.toml 缺失场景」**：spec 要求抛 FileNotFoundError 含修复指引，已通过 `config.py:12-16` 的代码静态检查确认；未做端到端测试。
- **未实测「token 缺失时 service 装配跳过 tushare」端到端行为**：依赖代码静态阅读与 1e0ae0b commit message「全部 service 层从 os.getenv 迁移到 has_tushare_token()」声明。
- **未审计 `daily_basic.volume_ratio` fallback 与 stk_factor_pro 的实际调用路径**：留作独立 backlog（建议 slug：`add-daily-basic-capability`）。
- **未实施 `tomllib.load()` 直接读盘扫描守护**：spec 未要求；可作为「configuration validator」backlog。

## Spec Drift

**Drift 1（待阶段 3 清理，强 handoff）**：
- `src/finance_data/cache/resolver.py:41` 仍调用 `os.environ.get("FINANCE_DATA_CACHE", "1")`，与 spec「项目配置必须以 config.toml 为唯一事实来源」+「残余环境变量读取必须显式追踪」违例。
- `src/finance_data/provider/akshare/_proxy.py:13,16` 仍调用 `os.environ.get("no_proxy", "")` 与 `os.environ["no_proxy"] = ...`，违例同上（注：写入 `no_proxy` 是为 akshare 内部消费，可保留写入但读取应来自 config.toml）。
- **处理**：不在本 retroactive 修代码（与 retroactive 纪律一致）。强 handoff 给阶段 3 `cleanup-config-and-proxy-leftovers` change，该 change 实施前必须先核对本 spec 的「可被显式关闭」(cache-layer) + 「残余环境变量读取必须显式追踪」(configuration) 两条 Requirement，确认实施方案符合 spec。

无其他 drift。1e0ae0b 中的「client.py 构造函数去掉 token / url 参数」是 API breaking，已发生且不可逆，spec 不需追溯（行为契约只覆盖前向）。

## 上游未对齐项

无。本 change 不接入任何上游金融数据源，纯配置规范沉淀。
