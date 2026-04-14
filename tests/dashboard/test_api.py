"""Tests for dashboard API endpoints"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from finance_data.dashboard.metrics import MetricsStore
from finance_data.dashboard.models import HealthResult
from finance_data.interface.types import DataResult


@pytest.fixture()
def tmp_metrics(tmp_path):
    """Create a MetricsStore backed by a temp DB"""
    store = MetricsStore(db_path=tmp_path / "test.db")
    return store


@pytest.fixture()
def client(tmp_metrics):
    """FastAPI test client with mocked metrics store"""
    from finance_data.dashboard import app as app_module

    app_module._metrics = tmp_metrics
    client = TestClient(app_module.app)
    yield client


class TestGetTools:
    def test_returns_list(self, client):
        resp = client.get("/api/tools")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_tool_has_required_fields(self, client):
        resp = client.get("/api/tools")
        tool = resp.json()[0]
        assert "name" in tool
        assert "description" in tool
        assert "domain" in tool
        assert "providers" in tool
        assert "params" in tool
        assert isinstance(tool["providers"], list)

    def test_tool_exposes_signature_params(self, client):
        resp = client.get("/api/tools")
        tools = {tool["name"]: tool for tool in resp.json()}
        suspend = tools["tool_get_suspend_daily"]
        assert suspend["params"] == [
            {"name": "date", "required": True, "default": None}
        ]

        board_daily = tools["tool_get_board_kline_history"]
        assert [param["name"] for param in board_daily["params"]] == [
            "board_name", "idx_type", "trade_date", "start_date", "end_date",
        ]

    def test_kline_tools_split_by_period(self, client):
        resp = client.get("/api/tools")
        tools = {tool["name"]: tool for tool in resp.json()}
        assert "tool_get_kline_daily_history" in tools
        assert "tool_get_kline_weekly_history" in tools
        assert "tool_get_kline_monthly_history" in tools
        assert "tool_get_kline_history" not in tools
        # 新工具不再有 period 参数
        daily = tools["tool_get_kline_daily_history"]
        param_names = [p["name"] for p in daily["params"]]
        assert "period" not in param_names


class TestGetProviders:
    def test_returns_list(self, client):
        resp = client.get("/api/providers")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        names = [p["name"] for p in data]
        assert "akshare" in names
        assert "tushare" in names
        assert "xueqiu" in names

    def test_akshare_always_available(self, client):
        resp = client.get("/api/providers")
        data = resp.json()
        akshare = next(p for p in data if p["name"] == "akshare")
        assert akshare["available"] is True


class TestHealthProbes:
    def test_health_all_returns_sse(self, client):
        mock_result = HealthResult(
            tool="tool_get_stock_quote_realtime",
            provider="akshare",
            status="ok",
            response_time_ms=150.0,
            record_count=1,
        )

        def mock_probes(tool_name=None):
            yield mock_result

        with patch("finance_data.dashboard.app.run_probes", mock_probes):
            resp = client.post("/api/health")
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers["content-type"]
            lines = resp.text.strip().split("\n")
            data_lines = [l for l in lines if l.startswith("data: ")]
            assert len(data_lines) >= 2  # result + [DONE]
            first = json.loads(data_lines[0].removeprefix("data: "))
            assert first["tool"] == "tool_get_stock_quote_realtime"
            assert first["status"] == "ok"
            assert data_lines[-1] == "data: [DONE]"

    def test_health_single_tool(self, client):
        mock_result = HealthResult(
            tool="tool_get_kline_history",
            provider="akshare",
            status="ok",
            response_time_ms=200.0,
        )

        def mock_probes(tool_name=None):
            yield mock_result

        with patch("finance_data.dashboard.app.run_probes", mock_probes):
            resp = client.post("/api/health/tool_get_kline_history")
            assert resp.status_code == 200

    def test_health_unknown_tool(self, client):
        resp = client.post("/api/health/nonexistent_tool")
        data = resp.json()
        assert "error" in data


class TestMetrics:
    def test_latest_empty(self, client):
        resp = client.get("/api/metrics/latest")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_latest_after_record(self, client, tmp_metrics):
        tmp_metrics.record("tool_test", "akshare", "ok", 100.0, source="probe")
        resp = client.get("/api/metrics/latest")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["tool"] == "tool_test"
        assert data[0]["status"] == "ok"

    def test_stats_empty(self, client):
        resp = client.get("/api/metrics/stats")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_stats_after_records(self, client, tmp_metrics):
        tmp_metrics.record("tool_a", "akshare", "ok", 100.0)
        tmp_metrics.record("tool_a", "akshare", "error", 50.0, error="fail")
        resp = client.get("/api/metrics/stats")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["total_calls"] == 2
        assert data[0]["success_count"] == 1
        assert data[0]["success_rate"] == 50.0

    def test_history(self, client, tmp_metrics):
        tmp_metrics.record("tool_b", "tushare", "ok", 200.0)
        tmp_metrics.record("tool_b", "tushare", "ok", 150.0)
        resp = client.get("/api/metrics/tool_b/tushare")
        data = resp.json()
        assert len(data) == 2

    def test_latest_filter_by_tool(self, client, tmp_metrics):
        tmp_metrics.record("tool_a", "akshare", "ok", 100.0)
        tmp_metrics.record("tool_b", "tushare", "ok", 200.0)
        resp = client.get("/api/metrics/latest?tool=tool_a")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["tool"] == "tool_a"


class TestInvokeTool:
    def test_unknown_tool(self, client):
        resp = client.post("/api/tools/nonexistent", json={"params": {}})
        data = resp.json()
        assert data["status"] == "error"
        assert "unknown" in data["error"]

    def test_invoke_success(self, client):
        mock_result = DataResult(
            data=[{"symbol": "000001", "name": "test"}],
            source="akshare",
            meta={},
        )
        mock_dispatcher = MagicMock()
        mock_dispatcher.get_realtime_quote.return_value = mock_result
        mock_module = MagicMock()
        mock_module.realtime_quote = mock_dispatcher

        with patch("importlib.import_module", return_value=mock_module):
            resp = client.post(
                "/api/tools/tool_get_stock_quote_realtime",
                json={"params": {"symbol": "000001"}},
            )
            data = resp.json()
            assert data["status"] == "ok"
            assert data["provider"] == "akshare"
            assert data["data"]["data"][0]["symbol"] == "000001"

    def test_invoke_daily_kline_symbol_only_applies_defaults(self, client):
        mock_result = DataResult(
            data=[{"symbol": "000001", "date": "20260409", "close": 11.1}],
            source="tushare",
            meta={},
        )
        mock_dispatcher = MagicMock()
        mock_dispatcher.get_daily_kline_history.return_value = mock_result
        mock_module = MagicMock()
        mock_module.daily_kline_history = mock_dispatcher

        with patch("importlib.import_module", return_value=mock_module):
            resp = client.post(
                "/api/tools/tool_get_kline_daily_history",
                json={"params": {"symbol": "000001"}},
            )
            data = resp.json()
            assert data["status"] == "ok"
            _, kwargs = mock_dispatcher.get_daily_kline_history.call_args
            assert kwargs["symbol"] == "000001"
            assert kwargs["start"] == "20240101"
            assert len(kwargs["end"]) == 8
            assert kwargs["adj"] == "qfq"

    def test_invoke_error(self, client):
        mock_module = MagicMock()
        mock_module.realtime_quote.get_realtime_quote.side_effect = Exception("network error")

        with patch("importlib.import_module", return_value=mock_module):
            resp = client.post(
                "/api/tools/tool_get_stock_quote_realtime",
                json={"params": {"symbol": "000001"}},
            )
            data = resp.json()
            assert data["status"] == "error"
            assert "network error" in data["error"]

    def test_invoke_direct_provider_board_member(self, client):
        mock_result = DataResult(
            data=[{"symbol": "601398", "name": "工商银行"}],
            source="tushare",
            meta={},
        )
        mock_instance = MagicMock()
        mock_instance.get_board_member.return_value = mock_result
        mock_cls = MagicMock(return_value=mock_instance)

        with patch(
                "finance_data.dashboard.health._import_class",
                return_value=mock_cls,
            ):
            with patch(
                "finance_data.dashboard.health.get_providers_for_tool",
                return_value=[
                    (
                        "tushare",
                        "finance_data.provider.tushare.board.member:TushareBoardMember",
                        "get_board_member",
                    )
                ],
            ):
                resp = client.post(
                    "/api/tools/tool_get_board_member_history",
                    json={"params": {"board_name": "银行", "idx_type": "行业板块"}, "provider": "tushare"},
                )

        data = resp.json()
        assert data["status"] == "ok"
        mock_instance.get_board_member.assert_called_once_with(
            board_name="银行",
            idx_type="行业板块",
            trade_date="",
            start_date="",
            end_date="",
        )

    def test_invoke_direct_provider_uses_registered_provider_even_if_health_filter_would_hide_it(self, client):
        mock_result = DataResult(
            data=[{"symbol": "000001", "date": "20260324"}],
            source="tushare",
            meta={},
        )
        mock_instance = MagicMock()
        mock_instance.get_daily_kline_history.return_value = mock_result
        mock_cls = MagicMock(return_value=mock_instance)

        with patch(
            "finance_data.dashboard.health._import_class",
            return_value=mock_cls,
        ):
            resp = client.post(
                "/api/tools/tool_get_kline_daily_history",
                json={
                    "params": {
                        "symbol": "000001",
                        "start": "20260324",
                        "end": "20260324",
                    },
                    "provider": "tushare",
                },
            )

        data = resp.json()
        assert data["status"] == "ok"
        assert data["provider"] == "tushare"
        mock_instance.get_daily_kline_history.assert_called_once_with(
            symbol="000001",
            start="20260324",
            end="20260324",
            adj="qfq",
        )

    def test_invoke_direct_provider_rejects_unregistered_provider(self, client):
        resp = client.post(
            "/api/tools/tool_get_kline_daily_history",
            json={
                "params": {
                    "symbol": "000001",
                    "start": "20260324",
                    "end": "20260324",
                },
                "provider": "not_real",
            },
        )

        data = resp.json()
        assert data["status"] == "error"
        assert "not registered" in data["error"]


class TestSPAFallback:
    def test_fallback_serves_spa(self, client):
        resp = client.get("/some/random/path")
        assert resp.status_code == 200
        # If static files exist, serves index.html; otherwise returns JSON
        content_type = resp.headers.get("content-type", "")
        if "text/html" in content_type:
            assert "<!doctype html>" in resp.text.lower() or "<html" in resp.text.lower()
        else:
            data = resp.json()
            assert "message" in data
