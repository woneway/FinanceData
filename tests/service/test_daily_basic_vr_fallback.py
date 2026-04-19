"""测试 daily_basic volume_ratio 从 stk_factor_pro fallback 补充"""
from unittest.mock import patch

from finance_data.interface.types import DataFetchError, DataResult
from finance_data.service.daily_basic import _fill_volume_ratio_from_factor


def _make_daily_basic_rows(volume_ratio=0.0):
    """构造 daily_basic 结果，volume_ratio 可控。"""
    return DataResult(
        data=[
            {"symbol": "000001.SZ", "trade_date": "20260416", "close": 10.0, "volume_ratio": volume_ratio},
            {"symbol": "600519.SH", "trade_date": "20260416", "close": 1800.0, "volume_ratio": volume_ratio},
        ],
        source="tushare",
        meta={"rows": 2, "trade_date": "20260416"},
    )


def _make_factor_result():
    """构造 stk_factor_pro 结果，volume_ratio 正常。"""
    return DataResult(
        data=[
            {"symbol": "000001", "trade_date": "20260416", "volume_ratio": 1.37},
            {"symbol": "600519", "trade_date": "20260416", "volume_ratio": 0.85},
        ],
        source="tushare",
        meta={},
    )


def test_fills_when_all_zero():
    """volume_ratio 全为 0 时，应从 stk_factor_pro 补充。"""
    result = _make_daily_basic_rows(volume_ratio=0.0)

    with patch("finance_data.service.technical.stock_factor") as mock_sf:
        mock_sf.get_stock_factor.return_value = _make_factor_result()
        filled = _fill_volume_ratio_from_factor(result, "20260416")

    assert filled.data[0]["volume_ratio"] == 1.37
    assert filled.data[1]["volume_ratio"] == 0.85


def test_skips_when_vr_present():
    """volume_ratio 已有正常值时，不应触发 fallback。"""
    result = _make_daily_basic_rows(volume_ratio=1.5)

    filled = _fill_volume_ratio_from_factor(result, "20260416")

    assert filled.data[0]["volume_ratio"] == 1.5
    assert filled.data[1]["volume_ratio"] == 1.5


def test_graceful_on_factor_failure():
    """stk_factor_pro 失败时，应返回原始结果不报错。"""
    result = _make_daily_basic_rows(volume_ratio=0.0)

    with patch("finance_data.service.technical.stock_factor") as mock_sf:
        mock_sf.get_stock_factor.side_effect = DataFetchError(
            "tushare", "stk_factor_pro", "timeout", "network"
        )
        filled = _fill_volume_ratio_from_factor(result, "20260416")

    assert filled.data[0]["volume_ratio"] == 0.0
    assert filled.data[1]["volume_ratio"] == 0.0


def test_partial_match():
    """factor 只覆盖部分票时，只补充匹配到的。"""
    result = DataResult(
        data=[
            {"symbol": "000001.SZ", "trade_date": "20260416", "close": 10.0, "volume_ratio": 0.0},
            {"symbol": "999999.SZ", "trade_date": "20260416", "close": 5.0, "volume_ratio": 0.0},
        ],
        source="tushare",
        meta={"rows": 2, "trade_date": "20260416"},
    )

    with patch("finance_data.service.technical.stock_factor") as mock_sf:
        mock_sf.get_stock_factor.return_value = _make_factor_result()
        filled = _fill_volume_ratio_from_factor(result, "20260416")

    assert filled.data[0]["volume_ratio"] == 1.37
    assert filled.data[1]["volume_ratio"] == 0.0  # 无匹配，保持原值
