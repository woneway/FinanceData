<!-- 用 openspec/templates/acceptance.template.md 落地。 -->

## 验收结论

变更 `cleanup-config-and-proxy-leftovers` 已完成实现和验证。三类残余配置遗留全部清理：`FINANCE_DATA_CACHE` 环境变量已迁至 `[cache] enabled`、`_proxy.py` 硬编码 hosts 已迁至 `[proxy] no_proxy_hosts`、`tests/conftest.py` 改用 monkeypatch helper。新建 `proxy-bypass` capability（3 条 Requirement）+ 守护测试自动化锁定「东财 provider 必须绕代理」不变量。`kline-history` REMOVED 1 条横切代理 Requirement，`configuration` / `cache-layer` MODIFIED 各自 Requirement 与新事实对齐。本 change 是阶段性优化路线图的第一个动代码 change，0 测试回归，全量 412 passed。

## Completeness

按 spec 增量逐条核对：

- 已实现 `proxy-bypass`「东财上游必须在 provider 模块顶部强制绕过本地代理」：6 个 akshare 东财 provider（lhb / lhb_inst_detail / suspend / hot_rank / north_flow / pool）继续保持 `ensure_eastmoney_no_proxy()` 调用；新 provider 接入约束由守护测试强制。
- 已实现 `proxy-bypass`「东财绕代理守护必须由自动化测试强制」：新增 `tests/provider/test_proxy_guard.py`，14 个用例（6 passed + 7 skipped + 1 元测试）；故意删除 `lhb/history.py` 的 `ensure_eastmoney_no_proxy` 已实测触发 FAIL，恢复后 PASSED。
- 已实现 `proxy-bypass`「no_proxy hosts 列表必须从 config.toml 读取」：`config.py` 新增 `get_no_proxy_hosts()` helper（缺省 `["eastmoney.com", ".eastmoney.com"]`）；`_proxy.py:ensure_eastmoney_no_proxy()` 内部改读该 helper，函数签名不变。
- 已实现 `configuration` MODIFIED「项目配置必须以 config.toml 为唯一事实来源」：src/ 下 `os.environ.get("FINANCE_DATA_*")` 已清零（仅 `config.py:50` 的 docstring 字符串引用，非代码读取）。
- 已实现 `configuration` MODIFIED「可选配置必须有明确的缺省语义」：`is_cache_enabled()` 缺省 True、`get_no_proxy_hosts()` 缺省含东财默认。
- 已实现 `cache-layer` MODIFIED「缓存层必须默认启用且可被显式关闭」：开关从 `FINANCE_DATA_CACHE=0` 迁至 `config.toml [cache] enabled = false`；conftest.py 通过 monkeypatch 实现测试关闭。
- 已实现 `kline-history` REMOVED「涉及东财上游的周期 K 线 fallback 必须配置代理绕过」：等价行为已在 `proxy-bypass` 第 1 条 Requirement 覆盖且扩展到所有 akshare 东财 provider。
- `config.toml.example` 增 `[cache]` 与 `[proxy]` 两段示例 + 注释；CLAUDE.md 配置章节同步更新含 breaking 迁移指引。

## Correctness

已执行并通过：

- `openspec validate cleanup-config-and-proxy-leftovers --strict` → `Change ... is valid`
- `pytest tests/provider/test_proxy_guard.py -v` → 7 passed, 7 skipped（首次跑，6 个东财 provider 全绿）
- 故意 strip `lhb/history.py` 的 `ensure_eastmoney_no_proxy` → 守护测试 FAILED（含 `lhb/history.py` 路径），恢复后再跑 → PASSED
- `pytest tests/` 全量四次：守护测试加入后 / config helper 加入后 / _proxy.py 改后 / cache resolver + conftest 改后 → **每次都是 412 passed, 8 skipped**（无回归）
- `.venv/bin/python -c "from finance_data.config import is_cache_enabled, get_no_proxy_hosts; print(is_cache_enabled(), get_no_proxy_hosts())"` → `True ['eastmoney.com', '.eastmoney.com']`
- 模拟调用 `ensure_eastmoney_no_proxy()` 三种场景（空 / 重复 / 已含其他域名）：均正确合并、幂等、不覆盖
- `grep -rn "FINANCE_DATA_CACHE\|os.environ.get" src/finance_data/` → 仅 2 处合规残留：`config.py:50` 是 docstring 字符串引用、`_proxy.py:17` 是 spec proxy-bypass 第 3 条 Requirement 显式允许的「写入 no_proxy 必需先读」行为
- `python3 -c "import tomllib; tomllib.load(open('config.toml.example','rb'))"` → 解析含 4 段 keys

未做 Playwright 验证：本 change 不涉及前端。

## Coherence

- `ensure_eastmoney_no_proxy()` 函数签名（无参、无返回）保持不变（与 design.md Decision 2 一致），6 个调用方零修改。
- `is_cache_enabled()` 缺省 True，与历史 `FINANCE_DATA_CACHE=1` 等价（与 design.md Decision 3 一致）。
- conftest.py 改用 monkeypatch helper 而非写临时 config.toml，最小副作用（与 design.md Decision 4 一致）。
- 守护测试用「文件级文本扫描 + 单词边界正则」而非真实 import，无网络副作用、无 import 顺序污染（与 design.md Decision 5 一致）。
- 守护测试白名单包含 `stock_zh_a_hist`（带单词边界后断言，避免误捕获 `stock_zh_a_hist_tx` 腾讯源 / `stock_zh_a_hist_em` 东财源 _em 后缀）（与 design.md Decision 6 一致 + 实测发现并修正）。
- `proxy-bypass` 单独成 capability，承接横切关注点，`kline-history` REMOVED 该 Requirement（与 design.md Decision 1 一致）。
- `cache-layer` MODIFIED 显式声明「FINANCE_DATA_CACHE 环境变量不再生效」Scenario，预防日后误用（与 design.md Decision 7 一致）。
- 阶段 2.4 retroactive-config-toml-consolidation 的 handoff drift 已 100% 清理，与 governance「drift 必须最终被修复」一致。

## 未测试项与风险

- **未实测「akshare 真实调用东财源时绕代理生效」端到端**：守护测试只锁「调用了 `ensure_eastmoney_no_proxy()`」这一前置条件；akshare 内部是否真的尊重 `no_proxy` 环境变量，依赖 akshare 实现（外部依赖，本 change 不验证）。
- **未实测「config.toml 中 [cache]/[proxy] 段被显式配置时」的端到端行为**：当前测试均跑 default 缺省路径；若用户在 config.toml 写 `[cache] enabled = false`，行为应正确禁用缓存，但本 change 未在测试中显式覆盖（依赖 helper 单元等价性）。
- **未审计「FINANCE_DATA_CACHE 环境变量在用户脚本/CI 中的实际依赖面」**：breaking 迁移指引已写入 CLAUDE.md，但未通知具体下游用户；建议未来定期 review 用户反馈。

## Spec Drift

无。本 change 把阶段 2.4 显式 handoff 的两项 drift（`FINANCE_DATA_CACHE` 残余 + `_proxy.py` 硬编码 hosts）全部清理；当前 src/ 下不再有未追踪的 `os.environ.get` 残余。

剩余两处 `os.environ` 引用均是 spec 显式允许：
- `config.py:50` — 仅 docstring 字符串「FINANCE_DATA_CACHE=1」用于历史等价说明，非代码读取。
- `_proxy.py:17` — `os.environ.get("no_proxy", "")` 是「写入前先读以保持幂等合并」，与 `proxy-bypass` 第 3 条 Requirement「仍 MUST 写入 `no_proxy` 环境变量（akshare 内部消费必需）」语义一致。

## 上游未对齐项

无。本 change 不接入任何上游金融数据源。
