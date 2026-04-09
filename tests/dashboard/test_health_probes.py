"""Tests for health probe date resolution and ProbeSpec enforcement."""
from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from finance_data.dashboard.health import (
    _recent_trade_date,
    _run_single_probe,
    resolve_probe_params,
)


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
        # Mock datetime.now to a Monday
        with patch("finance_data.dashboard.health.datetime") as mock_dt:
            # Monday 2026-04-06 → yesterday is Sunday → should skip to Friday 2026-04-03
            mock_dt.now.return_value = datetime(2026, 4, 6, 10, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            d = _recent_trade_date()
            assert d.weekday() == 4  # Friday

    def test_all_registry_probes_have_no_hardcoded_dates(self):
        """Ensure no probe in the registry uses hardcoded 20xx dates."""
        from finance_data.tool_specs import list_tool_specs

        hardcoded_pattern = re.compile(r"^20\d{6}$")
        violations = []
        for spec in list_tool_specs():
            for key, value in spec.probe.default_params.items():
                if isinstance(value, str) and hardcoded_pattern.match(value):
                    violations.append(f"{spec.name}.probe.{key}={value}")
        assert not violations, f"Hardcoded dates found in probes: {violations}"


# ------------------------------------------------------------------
# ProbeSpec enforcement in _run_single_probe
# ------------------------------------------------------------------

def _make_provider_class(data, source="test"):
    """Create a mock provider class that returns given data."""
    class MockProvider:
        def probe_method(self, **kwargs):
            result = MagicMock()
            result.data = data
            result.source = source
            result.meta = {}
            return result
    return MockProvider


class TestProbeSpecEnforcement:
    def test_min_records_violation_warns(self):
        """When returned records < min_records, status should be 'warn'."""
        spec_patch = MagicMock()
        spec_patch.default_params = {"symbol": "000001"}
        spec_patch.min_records = 5
        spec_patch.required_fields = ()
        spec_patch.timeout_sec = 30

        MockCls = _make_provider_class([{"symbol": "000001", "date": "20260409"}])

        with patch("finance_data.dashboard.health.get_tool_probe", return_value=spec_patch), \
             patch("finance_data.dashboard.health._import_class", return_value=MockCls):
            health_result, data = _run_single_probe(
                "test_tool", "test_provider",
                "fake.path:MockCls", "probe_method",
            )
        assert health_result.status == "warn"
        assert "min_records" in health_result.error

    def test_required_fields_missing_warns(self):
        """When required fields are absent from data, status should be 'warn'."""
        spec_patch = MagicMock()
        spec_patch.default_params = {"symbol": "000001"}
        spec_patch.min_records = 0
        spec_patch.required_fields = ("symbol", "price", "missing_field")
        spec_patch.timeout_sec = 30

        MockCls = _make_provider_class([{"symbol": "000001", "price": 10.5}])

        with patch("finance_data.dashboard.health.get_tool_probe", return_value=spec_patch), \
             patch("finance_data.dashboard.health._import_class", return_value=MockCls):
            health_result, data = _run_single_probe(
                "test_tool", "test_provider",
                "fake.path:MockCls", "probe_method",
            )
        assert health_result.status == "warn"
        assert "missing_field" in health_result.error

    def test_valid_probe_returns_ok(self):
        """When all invariants pass, status should be 'ok'."""
        spec_patch = MagicMock()
        spec_patch.default_params = {"symbol": "000001"}
        spec_patch.min_records = 1
        spec_patch.required_fields = ("symbol",)
        spec_patch.timeout_sec = 30

        MockCls = _make_provider_class([{"symbol": "000001", "price": 10.5}])

        with patch("finance_data.dashboard.health.get_tool_probe", return_value=spec_patch), \
             patch("finance_data.dashboard.health._import_class", return_value=MockCls):
            health_result, data = _run_single_probe(
                "test_tool", "test_provider",
                "fake.path:MockCls", "probe_method",
            )
        assert health_result.status == "ok"
        assert health_result.record_count == 1

    def test_empty_data_with_zero_min_records_is_ok(self):
        """min_records=0 should allow empty results."""
        spec_patch = MagicMock()
        spec_patch.default_params = {}
        spec_patch.min_records = 0
        spec_patch.required_fields = ()
        spec_patch.timeout_sec = 30

        MockCls = _make_provider_class([])

        with patch("finance_data.dashboard.health.get_tool_probe", return_value=spec_patch), \
             patch("finance_data.dashboard.health._import_class", return_value=MockCls):
            health_result, data = _run_single_probe(
                "test_tool", "test_provider",
                "fake.path:MockCls", "probe_method",
            )
        assert health_result.status == "ok"
        assert health_result.record_count == 0

    def test_timeout_returns_timeout_status(self):
        """When a provider exceeds timeout_sec, status should be 'timeout'."""
        spec_patch = MagicMock()
        spec_patch.default_params = {}
        spec_patch.min_records = 0
        spec_patch.required_fields = ()
        spec_patch.timeout_sec = 1  # 1 second timeout

        class SlowProvider:
            def probe_method(self, **kwargs):
                time.sleep(5)  # Way longer than timeout

        with patch("finance_data.dashboard.health.get_tool_probe", return_value=spec_patch), \
             patch("finance_data.dashboard.health._import_class", return_value=SlowProvider):
            health_result, data = _run_single_probe(
                "test_tool", "test_provider",
                "fake.path:SlowProvider", "probe_method",
            )
        assert health_result.status == "timeout"
        assert "timeout" in health_result.error
        assert data is None
