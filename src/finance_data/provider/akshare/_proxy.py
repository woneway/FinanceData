"""绕过代理访问东财 API。

代理（Clash/V2Ray 等）对东财 HTTPS 连接处理异常（SSL 错误），
需要将 eastmoney.com 加入 no_proxy 以直连。

hosts 列表来源：config.toml 的 [proxy] no_proxy_hosts。
仍写入 os.environ["no_proxy"]，因为 akshare 内部依赖该环境变量。
"""
import os

from finance_data.config import get_no_proxy_hosts


def ensure_eastmoney_no_proxy() -> None:
    """将 config.toml [proxy] no_proxy_hosts 合并到 no_proxy 环境变量（幂等）。"""
    hosts = get_no_proxy_hosts()
    existing = os.environ.get("no_proxy", "")
    existing_set = {h.strip() for h in existing.split(",") if h.strip()}
    missing = [h for h in hosts if h not in existing_set]
    if missing:
        parts = [p for p in [existing, ",".join(missing)] if p]
        os.environ["no_proxy"] = ",".join(parts)
