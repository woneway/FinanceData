from unittest.mock import patch

from finance_data.dashboard.health import get_providers_for_tool
from finance_data.tool_specs import get_tool_spec


def test_auction_close_documents_stock_minute_permission():
    spec = get_tool_spec("tool_get_auction_close_history")
    notes = " ".join(spec.metadata.limitations or ())

    assert spec.providers[0].available_if == "tushare_stock_minute_permission"
    assert "股票分钟权限" in notes


def test_auction_close_probe_requires_stock_minute_permission(monkeypatch):
    monkeypatch.delenv("TUSHARE_STOCK_MINUTE_PERMISSION", raising=False)
    with patch("finance_data.provider.tushare.client.is_token_valid", return_value=True), \
         patch("finance_data.provider.xueqiu.client.has_login_cookie", return_value=False):
        providers = get_providers_for_tool("tool_get_auction_close_history")

    assert providers == []


def test_auction_close_probe_available_with_stock_minute_permission(monkeypatch):
    monkeypatch.setenv("TUSHARE_STOCK_MINUTE_PERMISSION", "1")
    with patch("finance_data.provider.tushare.client.is_token_valid", return_value=True), \
         patch("finance_data.provider.xueqiu.client.has_login_cookie", return_value=False):
        providers = get_providers_for_tool("tool_get_auction_close_history")

    assert providers
    assert providers[0][0] == "tushare"
