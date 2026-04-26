## 1. 守护测试先行（在重命名前合入）

- [x] 1.1 新建 `tests/test_client_naming.py`：含三个测试 — 集合一致性 / alias 兼容性 / alias 新名存在性。当前未重命名代码下，「集合一致性测试」预计 FAIL（揭露 client 当前命名 drift），「alias 测试」也预计 FAIL（_DEPRECATED_ALIASES 还不存在）。
- [x] 1.2 跑 `pytest tests/test_client_naming.py -v` 确认两个测试 FAIL（揭露 drift），与本 change 完成后必须全部 PASS 形成对照。

## 2. client.py 加 _DEPRECATED_ALIASES + __getattr__

- [x] 2.1 在 `src/finance_data/client.py` 顶部加 `_DEPRECATED_ALIASES: dict[str, str]` 字典字面量，48 项「旧名 → 新名」（按 design.md 映射表）。
- [x] 2.2 在 `FinanceData` 类内加 `__getattr__(self, name)` 方法：若 `name in _DEPRECATED_ALIASES`，发出 `DeprecationWarning(f"fd.{name}() 已废弃，请改用 fd.{new_name}()")`，返回 `getattr(self, new_name)`；否则按 Python 默认抛 `AttributeError`。

## 3. 逐方法重命名（48 个）

- [x] 3.1 按 design.md 映射表把 client.py 中 48 个 `def old_name` 改为 `def new_name`。Method body / docstring / 签名 / 类型注解 zero-touch。
- [x] 3.2 跑 `python3 -c "from finance_data import FinanceData; fd = FinanceData(); print([m for m in dir(fd) if not m.startswith('_')])"` 确认 48 个方法名全部为新名。

## 4. 更新 CLAUDE.md 与测试

- [x] 4.1 更新 `CLAUDE.md` Python Library 示例段：`fd.kline_daily` → `fd.kline_daily_history`、`fd.board_member` → `fd.board_member_history`、`fd.quote` → `fd.stock_quote_realtime`、`fd.capital_flow` → `fd.capital_flow_realtime`。在示例下补一段「旧名仍可工作但发出 DeprecationWarning，请新代码使用新名」。
- [x] 4.2 更新 `tests/test_client_board.py`：`fd.board_member(...)` → `fd.board_member_history(...)`。验证：跑 `pytest tests/test_client_board.py -v` 通过。

## 5. 终验

- [x] 5.1 跑全量 `pytest tests/`：必须 415 → 418+ passed（新增守护 3 测试）。
- [x] 5.2 跑 `pytest tests/test_client_naming.py -v`：3 个测试 PASS。
- [x] 5.3 跑 `python3 -c "import warnings; warnings.simplefilter('always'); from finance_data import FinanceData; fd = FinanceData(); fd.quote('000001')"` 确认 DeprecationWarning 被发出（捕获或观察 stderr）。

## 6. 写 acceptance 并归档

- [x] 6.1 写 `acceptance.md`：Completeness 逐条对应 spec 3 条 ADDED Requirement；Correctness 列 pytest 命令 + 集合枚举 + warning 验证；Coherence 验证签名零变更、文档同步、alias 兼容；未测试项 / drift / 上游未对齐显式列出。
- [x] 6.2 `openspec validate unify-tool-naming-history-suffix --strict` 通过。
- [x] 6.3 `openspec archive unify-tool-naming-history-suffix -y`：已自动新增 `client-naming` capability (3 Req)。验证：`openspec list --specs` 显示 10 个 capability。
