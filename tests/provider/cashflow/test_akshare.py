"""akshare 个股资金流向测试 - 已禁用（依赖东财 stock_individual_fund_flow）"""
import pytest

pytestmark = pytest.mark.skip(reason="akshare cashflow 已禁用（东财源）")
