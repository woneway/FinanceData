"""验证 registry 中对数据源限制的文档标注"""
from finance_data.provider.metadata.registry import TOOL_REGISTRY


def test_margin_has_rzche_limitation():
    """融资融券汇总应标注 akshare rzche=0 限制"""
    meta = TOOL_REGISTRY["tool_get_margin_history"]
    notes = " ".join(meta.limitations or [])
    assert "rzche" in notes, f"margin 应标注 rzche 限制，got: {meta.limitations}"


def test_margin_detail_has_rqye_limitation():
    """融资融券明细应标注 akshare 融券数据缺失"""
    meta = TOOL_REGISTRY["tool_get_margin_detail_history"]
    notes = " ".join(meta.limitations or [])
    assert "rqye" in notes, f"margin_detail 应标注融券数据缺失，got: {meta.limitations}"


def test_north_stock_hold_has_quarterly_limitation():
    """北向持股应标注交易所改为季度披露"""
    meta = TOOL_REGISTRY["tool_get_north_hold_history"]
    notes = " ".join(meta.limitations or [])
    assert "季度" in notes, f"north_stock_hold 应标注季度披露限制，got: {meta.limitations}"
