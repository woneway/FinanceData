"""Tests for unified verify orchestrator."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from finance_data.verify import VerifyReport, VerifyResult, run_verify


def _mock_validators_all_pass():
    """Patch all validators to return empty (pass)."""
    return (
        patch("finance_data.tool_specs.validators.validate_tool_specs", return_value={}),
        patch("finance_data.tool_specs.validators.validate_service_targets", return_value={}),
        patch("finance_data.tool_specs.validators.validate_probe_params_against_mcp", return_value={}),
        patch("finance_data.provider.metadata.validator.validate_toolspec_registry_consistency", return_value=[]),
    )


def test_run_verify_all_pass():
    p1, p2, p3, p4 = _mock_validators_all_pass()
    with p1, p2, p3, p4:
        report = run_verify()
    assert report.passed is True
    assert len(report.results) == 4
    assert all(r.passed for r in report.results)


def test_run_verify_with_failures():
    p1 = patch("finance_data.tool_specs.validators.validate_tool_specs",
               return_value={"tool_x": ["missing description"]})
    p2 = patch("finance_data.tool_specs.validators.validate_service_targets", return_value={})
    p3 = patch("finance_data.tool_specs.validators.validate_probe_params_against_mcp", return_value={})
    p4 = patch("finance_data.provider.metadata.validator.validate_toolspec_registry_consistency", return_value=[])
    with p1, p2, p3, p4:
        report = run_verify()
    assert report.passed is False
    tool_specs_result = report.results[0]
    assert tool_specs_result.name == "tool_specs"
    assert tool_specs_result.passed is False
    assert any("missing description" in e for e in tool_specs_result.errors)


def test_run_verify_with_smoke():
    p1, p2, p3, p4 = _mock_validators_all_pass()

    mock_result = MagicMock()
    mock_result.data = [{"date": "20260409", "open": "1"}]
    mock_result.source = "akshare"

    def patched_smoke(tool_name):
        return VerifyResult(
            name=f"smoke:{tool_name}", passed=True,
            duration_ms=10.0, level="smoke",
        )

    with p1, p2, p3, p4, \
         patch("finance_data.verify._run_single_smoke", side_effect=patched_smoke):
        report = run_verify(include_smoke=True)

    assert report.passed is True
    smoke_results = [r for r in report.results if r.level == "smoke"]
    assert len(smoke_results) == 5


def test_smoke_network_failure_is_warn():
    p1, p2, p3, p4 = _mock_validators_all_pass()

    def patched_smoke(tool_name):
        return VerifyResult(
            name=f"smoke:{tool_name}", passed=True,
            errors=[f"WARN: network error for {tool_name}"],
            duration_ms=5.0, level="smoke",
        )

    with p1, p2, p3, p4, \
         patch("finance_data.verify._run_single_smoke", side_effect=patched_smoke):
        report = run_verify(include_smoke=True)

    smoke_results = [r for r in report.results if r.level == "smoke"]
    assert all(r.passed for r in smoke_results)
    assert all(any("WARN" in e for e in r.errors) for r in smoke_results)


def test_verify_report_json():
    report = VerifyReport(
        passed=True,
        results=[
            VerifyResult(name="test_check", passed=True, duration_ms=10.5),
        ],
    )
    data = json.loads(report.model_dump_json())
    assert data["passed"] is True
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "test_check"


def test_main_entry_point():
    """Verify python -m finance_data verify --json produces valid JSON."""
    import subprocess
    import sys

    ret = subprocess.run(
        [sys.executable, "-m", "finance_data", "verify", "--json"],
        capture_output=True, text=True, timeout=30,
    )
    assert ret.returncode == 0
    data = json.loads(ret.stdout)
    assert "passed" in data
    assert "results" in data
