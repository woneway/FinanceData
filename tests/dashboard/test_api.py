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
        assert isinstance(tool["providers"], list)


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
            tool="tool_get_realtime_quote",
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
            assert first["tool"] == "tool_get_realtime_quote"
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
                "/api/tools/tool_get_realtime_quote",
                json={"params": {"symbol": "000001"}},
            )
            data = resp.json()
            assert data["status"] == "ok"
            assert data["provider"] == "akshare"
            assert data["data"]["data"][0]["symbol"] == "000001"

    def test_invoke_error(self, client):
        mock_module = MagicMock()
        mock_module.realtime_quote.get_realtime_quote.side_effect = Exception("network error")

        with patch("importlib.import_module", return_value=mock_module):
            resp = client.post(
                "/api/tools/tool_get_realtime_quote",
                json={"params": {"symbol": "000001"}},
            )
            data = resp.json()
            assert data["status"] == "error"
            assert "network error" in data["error"]


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
