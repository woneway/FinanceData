"""验证 registry api_name 与实际 provider 调用的函数名一致"""
from finance_data.provider.metadata.registry import TOOL_REGISTRY


def test_realtime_api_name_matches_actual():
    """realtime 实际用 xueqiu quotec.json"""
    meta = TOOL_REGISTRY["tool_get_realtime_quote"]
    assert meta.api_name == "quotec.json", \
        f"实际用 xueqiu quotec.json，registry 写了 {meta.api_name}"


def test_index_quote_api_name_matches_actual():
    """index_quote 实际用 stock_zh_index_spot_sina，非 index_zh_a_spot_em"""
    meta = TOOL_REGISTRY["tool_get_index_quote_realtime"]
    assert meta.api_name == "stock_zh_index_spot_sina", \
        f"实际用 sina 源，registry 写了 {meta.api_name}"


def test_index_history_api_name_matches_actual():
    """index_history 实际用 stock_zh_index_daily_tx，非 index_zh_a_hist"""
    meta = TOOL_REGISTRY["tool_get_index_history"]
    assert meta.api_name == "stock_zh_index_daily_tx", \
        f"实际用腾讯源，registry 写了 {meta.api_name}"
