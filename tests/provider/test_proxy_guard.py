"""守护测试：东财上游 provider 必须在模块顶部调用 ensure_eastmoney_no_proxy()。

实现「proxy-bypass」capability 的「东财绕代理守护必须由自动化测试强制」Requirement。

约束：扫描 src/finance_data/provider/akshare/**/*.py，凡 import 含 _em 后缀
函数或已知走东财的 akshare 函数（如 stock_zh_a_hist），模块文本必须包含
ensure_eastmoney_no_proxy 调用，否则视为违例。
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

# 项目根目录（tests/provider/test_proxy_guard.py → 项目根）
_REPO_ROOT = Path(__file__).resolve().parents[2]
_AKSHARE_DIR = _REPO_ROOT / "src" / "finance_data" / "provider" / "akshare"

# 匹配 import 中含 _em 后缀的 akshare 函数（如 ak.xxx_em / from akshare import xxx_em）
_EM_PATTERN = re.compile(r"\b\w+_em\b")

# 已知走东财但无 _em 后缀的 akshare 函数白名单（详见 spec proxy-bypass）
_KNOWN_EASTMONEY_FUNCS = (
    "stock_zh_a_hist",  # akshare 周/月线 fallback 走东财
)

# 守护标记：模块文本中必须出现的代理绕过函数调用
_GUARD_MARKER = "ensure_eastmoney_no_proxy"


def _iter_provider_files() -> list[Path]:
    """遍历 akshare provider 目录下所有 .py（排除 _proxy.py 自身和 __init__.py）。"""
    files: list[Path] = []
    for py in _AKSHARE_DIR.rglob("*.py"):
        name = py.name
        if name in {"__init__.py", "_proxy.py"}:
            continue
        files.append(py)
    return files


def _module_uses_eastmoney(text: str) -> bool:
    """判断模块文本是否引用了东财相关函数。

    检测条件：
    - 文本中包含 _em 后缀的函数名（如 ak.stock_lhb_detail_em / stock_zh_a_hist_em）
    - 或包含 _KNOWN_EASTMONEY_FUNCS 中的函数名（必须是完整函数名，
      不可被作为前缀误匹配，例如 stock_zh_a_hist 不应匹配 stock_zh_a_hist_tx）
    """
    if _EM_PATTERN.search(text):
        return True
    for func in _KNOWN_EASTMONEY_FUNCS:
        if re.search(rf"\b{re.escape(func)}\b(?!_)", text):
            return True
    return False


@pytest.mark.parametrize("py_path", _iter_provider_files(), ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_eastmoney_provider_calls_ensure_no_proxy(py_path: Path) -> None:
    """凡引用东财函数的 provider 模块必须调用 ensure_eastmoney_no_proxy()。"""
    text = py_path.read_text(encoding="utf-8")
    if not _module_uses_eastmoney(text):
        pytest.skip(f"{py_path.relative_to(_REPO_ROOT)} 不引用东财函数，跳过守护")
    assert _GUARD_MARKER in text, (
        f"{py_path.relative_to(_REPO_ROOT)} 引用了东财函数但模块文本未出现 "
        f"`{_GUARD_MARKER}` 调用。请在模块顶部加 "
        f"`from finance_data.provider.akshare._proxy import ensure_eastmoney_no_proxy` "
        f"并在所有真实调用前 `ensure_eastmoney_no_proxy()`。"
    )


def test_proxy_guard_discovers_expected_files() -> None:
    """sanity check：守护测试至少能发现 6 个已知东财 provider 文件。

    这是元测试，防止 _iter_provider_files() 因路径调整或 glob 错误返回空集合，
    导致守护静默失效。
    """
    discovered = [p.relative_to(_REPO_ROOT).as_posix() for p in _iter_provider_files()]
    eastmoney_files = [
        p for p in discovered
        if _module_uses_eastmoney((_REPO_ROOT / p).read_text(encoding="utf-8"))
    ]
    assert len(eastmoney_files) >= 6, (
        f"期望发现至少 6 个东财 provider 文件，实际仅发现 {len(eastmoney_files)} 个：\n"
        + "\n".join(f"  - {f}" for f in eastmoney_files)
    )
