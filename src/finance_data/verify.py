"""Unified verify orchestrator.

Usage:
    python -m finance_data.verify [--json] [--smoke] [--dashboard]
    finance-data verify [--include-smoke] [--include-dashboard] [--json]
"""
from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Report models
# ------------------------------------------------------------------

class VerifyResult(BaseModel):
    """Single check result."""
    name: str
    passed: bool
    errors: list[str] = Field(default_factory=list)
    duration_ms: float = 0.0
    level: Literal["check", "smoke"] = "check"


class VerifyReport(BaseModel):
    """Aggregate verify report."""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    passed: bool = True
    results: list[VerifyResult] = Field(default_factory=list)


# ------------------------------------------------------------------
# Validator wrapper
# ------------------------------------------------------------------

def _run_timed(name: str, fn: Any, level: str = "check") -> VerifyResult:
    """Run a validator, time it, and normalize the output."""
    start = time.monotonic()
    try:
        raw = fn()
    except Exception as e:
        elapsed = round((time.monotonic() - start) * 1000, 1)
        return VerifyResult(
            name=name, passed=False, errors=[f"exception: {e!s}"[:200]],
            duration_ms=elapsed, level=level,
        )

    elapsed = round((time.monotonic() - start) * 1000, 1)

    # Normalize two validator return formats
    errors: list[str] = []
    if isinstance(raw, dict):
        # dict[str, list[str]] from tool_specs/validators.py
        for key, msgs in raw.items():
            for msg in msgs:
                errors.append(f"{key}: {msg}")
    elif isinstance(raw, list):
        # list[ValidationResult] from provider/metadata/validator.py
        for r in raw:
            if hasattr(r, "passed") and not r.passed:
                tool = getattr(r, "tool_name", "")
                message = getattr(r, "message", str(r))
                errors.append(f"{tool}: {message}" if tool else message)
    # else: unexpected type, treat as pass

    return VerifyResult(
        name=name, passed=len(errors) == 0, errors=errors,
        duration_ms=elapsed, level=level,
    )


# ------------------------------------------------------------------
# Smoke tests
# ------------------------------------------------------------------

_SMOKE_TOOLS = [
    "tool_get_trade_calendar_history",
    "tool_get_kline_history",
    "tool_get_sector_rank_realtime",
    "tool_get_index_quote_realtime",
    "tool_get_market_stats_realtime",
]


def _run_single_smoke(tool_name: str) -> VerifyResult:
    """Run a single tool through the service dispatcher."""
    from finance_data.dashboard.health import resolve_probe_params
    from finance_data.interface.types import DataFetchError
    from finance_data.tool_specs import get_tool_probe, get_tool_spec

    spec = get_tool_spec(tool_name)
    if spec is None:
        return VerifyResult(
            name=f"smoke:{tool_name}", passed=False,
            errors=[f"ToolSpec not found: {tool_name}"], level="smoke",
        )

    probe = get_tool_probe(tool_name)
    raw_params = dict(probe.default_params) if probe else {}
    params = resolve_probe_params(raw_params)
    target = spec.service

    start = time.monotonic()
    try:
        mod = importlib.import_module(target.module_path)
        dispatcher = getattr(mod, target.object_name)
        method = getattr(dispatcher, target.method_name)
        result = method(**params)
        elapsed = round((time.monotonic() - start) * 1000, 1)

        errors: list[str] = []
        data = result.data if hasattr(result, "data") else []
        if not data:
            errors.append("WARN: empty data returned")

        if data and spec.return_fields:
            missing = [f for f in spec.return_fields if f not in data[0]]
            if missing:
                errors.append(f"WARN: missing return_fields {missing}")

        return VerifyResult(
            name=f"smoke:{tool_name}", passed=True,
            errors=errors, duration_ms=elapsed, level="smoke",
        )

    except (DataFetchError, ConnectionError, TimeoutError, OSError) as e:
        elapsed = round((time.monotonic() - start) * 1000, 1)
        return VerifyResult(
            name=f"smoke:{tool_name}", passed=True,
            errors=[f"WARN: {type(e).__name__}: {e!s}"[:200]],
            duration_ms=elapsed, level="smoke",
        )
    except Exception as e:
        elapsed = round((time.monotonic() - start) * 1000, 1)
        return VerifyResult(
            name=f"smoke:{tool_name}", passed=False,
            errors=[f"{type(e).__name__}: {e!s}"[:200]],
            duration_ms=elapsed, level="smoke",
        )


def _run_smoke_tests() -> list[VerifyResult]:
    return [_run_single_smoke(t) for t in _SMOKE_TOOLS]


# ------------------------------------------------------------------
# Main orchestrator
# ------------------------------------------------------------------

def run_verify(
    include_smoke: bool = False,
    include_dashboard: bool = False,
) -> VerifyReport:
    """Run all verification checks and return a structured report."""
    from finance_data.tool_specs.validators import (
        validate_probe_params_against_mcp,
        validate_service_targets,
        validate_tool_specs,
    )
    from finance_data.provider.metadata.validator import validate_toolspec_registry_consistency

    results: list[VerifyResult] = []

    results.append(_run_timed("tool_specs", validate_tool_specs))
    results.append(_run_timed("service_targets", validate_service_targets))
    results.append(_run_timed("probe_params", validate_probe_params_against_mcp))
    results.append(_run_timed("toolspec_registry", validate_toolspec_registry_consistency))

    if include_dashboard:
        from finance_data.tool_specs.validators import validate_dashboard_tools_api_against_registry
        results.append(_run_timed("dashboard_api", validate_dashboard_tools_api_against_registry))

    if include_smoke:
        results.extend(_run_smoke_tests())

    passed = all(r.passed for r in results)
    return VerifyReport(passed=passed, results=results)


# ------------------------------------------------------------------
# Output
# ------------------------------------------------------------------

def print_report(report: VerifyReport, as_json: bool = False) -> None:
    """Print report as JSON or rich table."""
    if as_json:
        import json
        print(report.model_dump_json(indent=2))
        return

    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Verify Report")
    table.add_column("Check", style="cyan")
    table.add_column("Level")
    table.add_column("Status")
    table.add_column("Time (ms)", justify="right")
    table.add_column("Errors", justify="right")

    for r in report.results:
        status = "[green]PASS[/green]" if r.passed else "[red]FAIL[/red]"
        table.add_row(r.name, r.level, status, str(r.duration_ms), str(len(r.errors)))
    console.print(table)

    if not report.passed:
        console.print("\n[bold]Error details:[/bold]")
        for r in report.results:
            if r.errors:
                for err in r.errors:
                    color = "yellow" if err.startswith("WARN") else "red"
                    console.print(f"  [{color}]{r.name}[/{color}]: {err}")

    if report.passed:
        console.print("\n[bold green]All checks passed.[/bold green]")
    else:
        console.print("\n[bold red]Some checks failed.[/bold red]")


# ------------------------------------------------------------------
# Script entry: python -m finance_data.verify
# ------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="FinanceData verify")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--smoke", action="store_true", help="Run smoke tests")
    parser.add_argument("--dashboard", action="store_true", help="Include dashboard check")
    args = parser.parse_args()

    report = run_verify(include_smoke=args.smoke, include_dashboard=args.dashboard)
    print_report(report, as_json=args.json)
    sys.exit(0 if report.passed else 1)
