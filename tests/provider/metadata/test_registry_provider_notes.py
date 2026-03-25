"""验证 registry 中对数据源限制的文档标注"""
from finance_data.provider.metadata.registry import TOOL_REGISTRY


def test_margin_has_rzche_limitation():
    """融资融券汇总应标注 akshare rzche=0 限制"""
    meta = TOOL_REGISTRY["tool_get_margin"]
    notes = " ".join(meta.limitations or [])
    assert "rzche" in notes, f"margin 应标注 rzche 限制，got: {meta.limitations}"


def test_margin_detail_has_rqye_limitation():
    """融资融券明细应标注 akshare 融券数据缺失"""
    meta = TOOL_REGISTRY["tool_get_margin_detail"]
    notes = " ".join(meta.limitations or [])
    assert "rqye" in notes, f"margin_detail 应标注融券数据缺失，got: {meta.limitations}"


def test_north_stock_hold_has_tushare_zero_fields():
    """北向持股应标注 tushare 多字段为 0"""
    meta = TOOL_REGISTRY["tool_get_north_stock_hold"]
    notes = " ".join(meta.limitations or [])
    assert "close_price" in notes, f"north_stock_hold 应标注 tushare 零值字段，got: {meta.limitations}"
