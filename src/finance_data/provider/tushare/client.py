"""tushare pro API 客户端初始化（共享）"""
import os
import tushare as ts

from finance_data.interface.types import DataFetchError


def get_pro():
    """初始化 tushare pro API，token 和 API URL 从环境变量读取。"""
    token = os.environ.get("TUSHARE_TOKEN", "")
    if not token:
        raise DataFetchError(
            source="tushare",
            func="init",
            reason="TUSHARE_TOKEN 环境变量未设置",
            kind="auth",
        )
    pro = ts.pro_api(token=token)
    api_url = os.environ.get("TUSHARE_API_URL", "")
    if api_url:
        pro._DataApi__token = token
        pro._DataApi__http_url = api_url
    return pro
