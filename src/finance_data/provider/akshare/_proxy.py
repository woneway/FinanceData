"""绕过代理访问东财 API。

代理（Clash/V2Ray 等）对东财 HTTPS 连接处理异常（SSL 错误），
需要将 eastmoney.com 加入 no_proxy 以直连。
"""
import os

_EASTMONEY_DOMAINS = "eastmoney.com,.eastmoney.com"


def ensure_eastmoney_no_proxy() -> None:
    """将 eastmoney.com 加入 no_proxy 环境变量（幂等）。"""
    no_proxy = os.environ.get("no_proxy", "")
    if "eastmoney.com" not in no_proxy:
        parts = [p for p in [no_proxy, _EASTMONEY_DOMAINS] if p]
        os.environ["no_proxy"] = ",".join(parts)
