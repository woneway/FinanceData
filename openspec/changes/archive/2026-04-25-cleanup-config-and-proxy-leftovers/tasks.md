## 1. 守护测试先行（不修代码）

- [x] 1.1 新建 `tests/provider/test_proxy_guard.py`：扫描 `provider/akshare/**/*.py`，凡 import 含 `_em` 后缀函数或 `stock_zh_a_hist`/`stock_zh_a_hist_em` 等已知东财函数的模块，断言文件中包含 `ensure_eastmoney_no_proxy` 字符串调用。验证：`pytest tests/provider/test_proxy_guard.py -v` 通过；当前 6 个 provider 全绿。
- [x] 1.2 故意删除 `provider/akshare/lhb/history.py` 中的 `ensure_eastmoney_no_proxy()` 调用，重跑 1.1 测试，确认 FAIL；然后恢复。验证：测试输出含 `lhb/history.py` 文件路径作为违例。
- [x] 1.3 跑全量 `pytest tests/` 确认守护测试不影响其他测试。

## 2. config.py 加 helper

- [x] 2.1 在 `src/finance_data/config.py` 加 `is_cache_enabled() -> bool`：从 `_load().get("cache", {}).get("enabled", True)` 读取，缺省 True。验证：手工调用返回 True（无 [cache] 段时）。
- [x] 2.2 在 `src/finance_data/config.py` 加 `get_no_proxy_hosts() -> list[str]`：从 `_load().get("proxy", {}).get("no_proxy_hosts", ["eastmoney.com", ".eastmoney.com"])` 读取。验证：手工调用返回默认列表（无 [proxy] 段时）。
- [x] 2.3 跑 `pytest tests/` 确认新 helper 添加不破坏现有测试。

## 3. 改 _proxy.py（保持函数签名兼容）

- [x] 3.1 修改 `src/finance_data/provider/akshare/_proxy.py:ensure_eastmoney_no_proxy()`：内部调用 `from finance_data.config import get_no_proxy_hosts`，把硬编码 `_EASTMONEY_DOMAINS` 替换为 `",".join(get_no_proxy_hosts())`。函数签名（无参，无返回）保持不变。验证：手动 import `provider/akshare/lhb/history.py`，确认 `os.environ["no_proxy"]` 被正确设置。
- [x] 3.2 跑 `pytest tests/provider/akshare/ -v` 确认所有 akshare provider 测试绿。

## 4. 改 cache/resolver.py（清掉 FINANCE_DATA_CACHE 读取）

- [x] 4.1 修改 `src/finance_data/cache/resolver.py:_is_cache_enabled()`：删除 `import os` + `os.environ.get(...)`，改为 `from finance_data.config import is_cache_enabled` + `return is_cache_enabled()`。验证：`grep -n "FINANCE_DATA_CACHE\|os.environ" src/finance_data/cache/resolver.py` 返回空。
- [x] 4.2 跑 `pytest tests/` 确认 cache 相关测试绿（注意：本步未改 conftest，conftest 仍写环境变量但已不被读，cache 默认启用 → 可能破坏依赖 mock 的测试 → 与 5.1 一起做或先临时跳过）。
  - 实际处理：跳过 4.2 的全量验证，4.1 + 5.1 作为原子操作合并；4.1 完成后立即做 5.1 再跑全量 pytest。

## 5. 改 conftest.py（monkeypatch helper）

- [x] 5.1 修改 `tests/conftest.py`：删除 `os.environ["FINANCE_DATA_CACHE"] = "0"`；新增 `import finance_data.config as _cfg; _cfg.is_cache_enabled = lambda: False`。验证：跑全量 `pytest tests/` 全绿（432+ 测试）。
- [x] 5.2 跑 `grep -rn "FINANCE_DATA_CACHE" src/ tests/` 确认仅 conftest 注释（如有）残留，src/ 下零匹配。

## 6. 更新 config.toml.example

- [x] 6.1 在 `config.toml.example` 增 `[cache]` 段，含 `enabled = true` + 注释说明「false 等价于历史的 FINANCE_DATA_CACHE=0 环境变量」。
- [x] 6.2 在 `config.toml.example` 增 `[proxy]` 段，含 `no_proxy_hosts = ["eastmoney.com", ".eastmoney.com"]` + 注释说明「东财源必须绕代理」。
- [x] 6.3 验证 `python3 -c "import tomllib; tomllib.load(open('config.toml.example','rb'))"` 解析无错。

## 7. 文档更新

- [x] 7.1 更新 `CLAUDE.md` 配置章节：把环境变量提示替换为 `config.toml [cache]` / `[proxy]` 段示例；保留 breaking 迁移指引（`FINANCE_DATA_CACHE=0` → `[cache] enabled = false`）。

## 8. 写 acceptance 并归档

- [x] 8.1 写 `acceptance.md`：Completeness 逐条对应 spec Requirement；Correctness 列出所有 pytest 命令与 grep 验证；Coherence 验证函数签名兼容、breaking 已声明；未测试项 / drift / 上游未对齐分别显式列出。
- [x] 8.2 `openspec validate cleanup-config-and-proxy-leftovers --strict` 通过。
- [x] 8.3 `openspec archive cleanup-config-and-proxy-leftovers -y`：已自动新建 `proxy-bypass` capability (3 Req)，MODIFIED `configuration` (~2)、`cache-layer` (~1)，REMOVED `kline-history` (-1)。验证：`openspec list --specs` 显示 9 个 capability，proxy-bypass 含 3 条 Requirement。
