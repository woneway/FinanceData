"""akshare 实时行情测试 - 已禁用（东财源不可用，新浪源太慢）"""
import pytest

pytestmark = pytest.mark.skip(reason="akshare realtime 已禁用（东财源）")
