"""akshare 个股基本信息测试 - 已禁用（依赖东财 stock_individual_basic_info_xq 内部 token）"""
import pytest

pytestmark = pytest.mark.skip(reason="akshare stock_info 已禁用（东财源）")
