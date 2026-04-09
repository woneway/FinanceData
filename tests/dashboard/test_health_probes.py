"""Tests for health probe date resolution, ProbeSpec enforcement, and Phase 3 upgrades."""
from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from finance_data.dashboard.health import (
    _check_schema,
    _recent_trade_date,
    _run_service_probe,
    _run_single_probe,
    resolve_probe_params,
)
from finance_data.dashboard.models import HealthResult
from finance_data.interface.types import DataFetchError


# ------------------------------------------------------------------
# resolve_probe_params
# ------------------------------------------------------------------

class TestResolveProbeParams:
    def test_recent_resolves_to_yyyymmdd(self):
        result = resolve_probe_params({"date": "$RECENT"})
        assert re.match(r"^\d{8}$", result["date"])

    def test_recent_with_offset(self):
        result = resolve_probe_params({"start": "$RECENT-30", "end": "$RECENT"})
        start = datetime.strptime(result["start"], "%Y%m%d")
        end = datetime.strptime(result["end"], "%Y%m%d")
        assert (end - start).days == 30

    def test_non_placeholder_unchanged(self):
        result = resolve_probe_params({"symbol": "000001", "period": "daily"})
        assert result == {"symbol": "000001", "period": "daily"}

    def test_mixed_params(self):
        result = resolve_probe_params({
            "symbol": "000001",
            "start": "$RECENT-7",
            "end": "$RECENT",
        })
        assert result["symbol"] == "000001"
        assert re.match(r"^\d{8}$", result["start"])
        assert re.match(r"^\d{8}$", result["end"])

    def test_recent_trade_date_skips_weekends(self):
        with patch("finance_data.dashboard.health.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 6, 10, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            d = _recent_trade_date()
            assert d.weekday() == 4  # Friday

    def test_all_registry_probes_have_no_hardcoded_dates(self):
        from finance_data.tool_specs import list_tool_specs
        hardcoded_pattern = re.compile(r"^20\d{6}$")
        violations = []
        for spec in list_tool_specs():
            for key, value in spec.probe.default_params.items():
                if isinstance(value, str) and hardcoded_pattern.match(value):
                    violations.append(f"{spec.name}.probe.{key}={value}")
        assert not violations, f"Hardcoded dates found in probes: {violations}"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_probe(
    default_params=None, min_records=0, required_fields=(), timeout_sec=30,
):
    probe = MagicMock()
    probe.default_params = default_params or {}
    probe.min_records = min_records
    probe.required_fields = required_fields
    probe.timeout_sec = timeout_sec
    return probe


def _make_provider_class(data, source="test"):
    class MockProvider:
        def probe_method(self, **kwargs):
            result = MagicMock()
            result.data = data
            result.source = source
            result.meta = {}
            return result
    return MockProvider


def _patch_probe_and_class(probe, cls):
    return (
        patch("finance_data.dashboard.health.get_tool_probe", return_value=probe),
        patch("finance_data.dashboard.health._import_class", return_value=cls),
    )


# ------------------------------------------------------------------
# ProbeSpec enforcement in _run_single_probe
# ------------------------------------------------------------------

class TestProbeSpecEnforcement:
    def test_min_records_violation_warns(self):
        probe = _make_probe(default_params={"symbol": "000001"}, min_records=5)
        MockCls = _make_provider_class([{"symbol": "000001", "date": "20260409"}])
        p1, p2 = _patch_probe_and_class(probe, MockCls)
        with p1, p2:
            hr, data = _run_single_probe("test_tool", "test_provider", "x:X", "probe_method")
        assert hr.status == "warn"
        assert "min_records" in hr.error
        assert hr.error_kind == "data"

    def test_required_fields_missing_warns(self):
        probe = _make_probe(default_params={"symbol": "000001"}, required_fields=("symbol", "missing"))
        MockCls = _make_provider_class([{"symbol": "000001", "price": 10.5}])
        p1, p2 = _patch_probe_and_class(probe, MockCls)
        with p1, p2:
            hr, _ = _run_single_probe("test_tool", "test_provider", "x:X", "probe_method")
        assert hr.status == "warn"
        assert "missing" in hr.error
        assert hr.error_kind == "data"

    def test_valid_probe_returns_ok(self):
        probe = _make_probe(default_params={"symbol": "000001"}, min_records=1, required_fields=("symbol",))
        MockCls = _make_provider_class([{"symbol": "000001", "price": 10.5}])
        p1, p2 = _patch_probe_and_class(probe, MockCls)
        with p1, p2:
            hr, _ = _run_single_probe("test_tool", "test_provider", "x:X", "probe_method")
        assert hr.status == "ok"
        assert hr.layer == "provider"

    def test_empty_data_with_zero_min_records_is_ok(self):
        probe = _make_probe()
        MockCls = _make_provider_class([])
        p1, p2 = _patch_probe_and_class(probe, MockCls)
        with p1, p2:
            hr, _ = _run_single_probe("test_tool", "test_provider", "x:X", "probe_method")
        assert hr.status == "ok"
        assert hr.record_count == 0

    def test_timeout_returns_timeout_status(self):
        probe = _make_probe(timeout_sec=1)
        class SlowProvider:
            def probe_method(self, **kwargs):
                time.sleep(5)
        p1 = patch("finance_data.dashboard.health.get_tool_probe", return_value=probe)
        p2 = patch("finance_data.dashboard.health._import_class", return_value=SlowProvider)
        with p1, p2:
            hr, data = _run_single_probe("test_tool", "test_provider", "x:X", "probe_method")
        assert hr.status == "timeout"
        assert hr.error_kind == "timeout"
        assert data is None


# ------------------------------------------------------------------
# Phase 3: error_kind mapping
# ------------------------------------------------------------------

class TestErrorKindMapping:
    def test_datafetcherror_auth_maps_to_error_kind(self):
        probe = _make_probe(default_params={"symbol": "000001"})
        class AuthFailProvider:
            def probe_method(self, **kwargs):
                raise DataFetchError("test", "probe_method", "token invalid", "auth")
        p1 = patch("finance_data.dashboard.health.get_tool_probe", return_value=probe)
        p2 = patch("finance_data.dashboard.health._import_class", return_value=AuthFailProvider)
        with p1, p2:
            hr, _ = _run_single_probe("test_tool", "test_provider", "x:X", "probe_method")
        assert hr.status == "error"
        assert hr.error_kind == "auth"
        assert hr.layer == "provider"

    def test_datafetcherror_data_maps_to_warn(self):
        probe = _make_probe(default_params={"symbol": "000001"})
        class NoDataProvider:
            def probe_method(self, **kwargs):
                raise DataFetchError("test", "probe_method", "无数据", "data")
        p1 = patch("finance_data.dashboard.health.get_tool_probe", return_value=probe)
        p2 = patch("finance_data.dashboard.health._import_class", return_value=NoDataProvider)
        with p1, p2:
            hr, _ = _run_single_probe("test_tool", "test_provider", "x:X", "probe_method")
        assert hr.status == "warn"
        assert hr.error_kind == "data"

    def test_datafetcherror_network_maps_to_error(self):
        probe = _make_probe(default_params={"symbol": "000001"})
        class NetFailProvider:
            def probe_method(self, **kwargs):
                raise DataFetchError("test", "probe_method", "connection refused", "network")
        p1 = patch("finance_data.dashboard.health.get_tool_probe", return_value=probe)
        p2 = patch("finance_data.dashboard.health._import_class", return_value=NetFailProvider)
        with p1, p2:
            hr, _ = _run_single_probe("test_tool", "test_provider", "x:X", "probe_method")
        assert hr.status == "error"
        assert hr.error_kind == "network"


# ------------------------------------------------------------------
# Phase 3: schema_ok
# ------------------------------------------------------------------

class TestSchemaOk:
    def test_schema_ok_true_when_all_return_fields_present(self):
        probe = _make_probe(default_params={"symbol": "000001"})
        data = [{"symbol": "000001", "name": "Test", "price": 10, "pct_chg": 1, "volume": 100, "amount": 1000}]
        MockCls = _make_provider_class(data)
        spec_mock = MagicMock()
        spec_mock.return_fields = ("symbol", "name", "price")

        p1 = patch("finance_data.dashboard.health.get_tool_probe", return_value=probe)
        p2 = patch("finance_data.dashboard.health._import_class", return_value=MockCls)
        p3 = patch("finance_data.dashboard.health.get_tool_spec", return_value=spec_mock)
        with p1, p2, p3:
            hr, _ = _run_single_probe("test_tool", "test_provider", "x:X", "probe_method")
        assert hr.schema_ok is True
        assert hr.status == "ok"

    def test_schema_ok_false_when_return_fields_missing(self):
        probe = _make_probe(default_params={"symbol": "000001"})
        data = [{"symbol": "000001", "name": "Test"}]
        MockCls = _make_provider_class(data)
        spec_mock = MagicMock()
        spec_mock.return_fields = ("symbol", "name", "price", "volume")

        p1 = patch("finance_data.dashboard.health.get_tool_probe", return_value=probe)
        p2 = patch("finance_data.dashboard.health._import_class", return_value=MockCls)
        p3 = patch("finance_data.dashboard.health.get_tool_spec", return_value=spec_mock)
        with p1, p2, p3:
            hr, _ = _run_single_probe("test_tool", "test_provider", "x:X", "probe_method")
        assert hr.schema_ok is False
        assert hr.error_kind == "schema"
        assert hr.status == "warn"

    def test_schema_ok_none_when_empty_data(self):
        probe = _make_probe()
        MockCls = _make_provider_class([])
        p1, p2 = _patch_probe_and_class(probe, MockCls)
        with p1, p2:
            hr, _ = _run_single_probe("test_tool", "test_provider", "x:X", "probe_method")
        assert hr.schema_ok is None
        assert hr.status == "ok"

    def test_check_schema_function(self):
        spec_mock = MagicMock()
        spec_mock.return_fields = ("a", "b", "c")
        with patch("finance_data.dashboard.health.get_tool_spec", return_value=spec_mock):
            assert _check_schema("t", [{"a": 1, "b": 2, "c": 3}]) is True
            assert _check_schema("t", [{"a": 1, "b": 2}]) is False
            assert _check_schema("t", []) is None


# ------------------------------------------------------------------
# Phase 3: service probe
# ------------------------------------------------------------------

class TestServiceProbe:
    def test_service_probe_success(self):
        probe = _make_probe(default_params={"symbol": "000001"})
        spec_mock = MagicMock()
        spec_mock.service.module_path = "fake.module"
        spec_mock.service.object_name = "dispatcher"
        spec_mock.service.method_name = "get_data"
        spec_mock.return_fields = ("symbol",)

        mock_result = MagicMock()
        mock_result.data = [{"symbol": "000001"}]
        mock_result.source = "akshare"

        mock_dispatcher = MagicMock()
        mock_dispatcher.get_data.return_value = mock_result
        mock_module = MagicMock()
        mock_module.dispatcher = mock_dispatcher

        with patch("finance_data.dashboard.health.get_tool_probe", return_value=probe), \
             patch("finance_data.dashboard.health.get_tool_spec", return_value=spec_mock), \
             patch("importlib.import_module", return_value=mock_module):
            hr = _run_service_probe("test_tool")
        assert hr.layer == "service"
        assert hr.status == "ok"
        assert hr.provider == "akshare"
        assert hr.record_count == 1

    def test_service_probe_datafetcherror(self):
        probe = _make_probe(default_params={"symbol": "000001"})
        spec_mock = MagicMock()
        spec_mock.service.module_path = "fake.module"
        spec_mock.service.object_name = "dispatcher"
        spec_mock.service.method_name = "get_data"

        mock_dispatcher = MagicMock()
        mock_dispatcher.get_data.side_effect = DataFetchError("all", "get_data", "all failed", "data")
        mock_module = MagicMock()
        mock_module.dispatcher = mock_dispatcher

        with patch("finance_data.dashboard.health.get_tool_probe", return_value=probe), \
             patch("finance_data.dashboard.health.get_tool_spec", return_value=spec_mock), \
             patch("importlib.import_module", return_value=mock_module):
            hr = _run_service_probe("test_tool")
        assert hr.layer == "service"
        assert hr.status == "warn"
        assert hr.error_kind == "data"

    def test_service_probe_no_toolspec(self):
        with patch("finance_data.dashboard.health.get_tool_spec", return_value=None):
            hr = _run_service_probe("nonexistent")
        assert hr.layer == "service"
        assert hr.status == "error"


# ------------------------------------------------------------------
# Phase 3: backward compatibility
# ------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_health_result_defaults(self):
        hr = HealthResult(tool="t", provider="p", status="ok")
        assert hr.layer == "provider"
        assert hr.error_kind is None
        assert hr.schema_ok is None
