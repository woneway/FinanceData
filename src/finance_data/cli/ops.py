"""Health probe and verification commands."""
from __future__ import annotations

import json
import subprocess
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


# ------------------------------------------------------------------
# finance-data health
# ------------------------------------------------------------------

@click.command()
@click.argument("tool", required=False, default=None)
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
def health_cmd(tool: str | None, as_json: bool) -> None:
    """Run health probes for all tools or a specific tool."""
    from finance_data.dashboard.health import run_probes
    from finance_data.dashboard.models import ConsistencyResult, HealthResult
    from finance_data.tool_specs import get_tool_spec

    if tool is not None and get_tool_spec(tool) is None:
        click.echo(f"Error: unknown tool '{tool}'", err=True)
        sys.exit(1)

    results: list[dict] = []
    probe_table = Table(title="Health Probes")
    probe_table.add_column("Tool", style="cyan", no_wrap=True)
    probe_table.add_column("Provider")
    probe_table.add_column("Status")
    probe_table.add_column("Time (ms)", justify="right")
    probe_table.add_column("Records", justify="right")
    probe_table.add_column("Error")

    consistency_results: list[dict] = []

    for result in run_probes(tool_name=tool):
        if isinstance(result, HealthResult):
            if as_json:
                results.append(result.model_dump())
            else:
                status_map = {
                    "ok": "[green]ok[/green]",
                    "warn": "[yellow]warn[/yellow]",
                    "error": "[red]error[/red]",
                    "timeout": "[red]timeout[/red]",
                }
                probe_table.add_row(
                    result.tool,
                    result.provider,
                    status_map.get(result.status, result.status),
                    str(result.response_time_ms),
                    str(result.record_count),
                    result.error or "",
                )
        elif isinstance(result, ConsistencyResult):
            if as_json:
                consistency_results.append(result.model_dump())
            else:
                status_map = {
                    "consistent": "[green]consistent[/green]",
                    "warn": "[yellow]warn[/yellow]",
                    "error": "[red]error[/red]",
                }
                status = status_map.get(result.status, result.status)
                providers = ", ".join(result.providers_compared)
                counts = ", ".join(f"{k}={v}" for k, v in result.record_counts.items())
                detail = f"providers: {providers}\nrecord_counts: {counts}"
                if result.diffs:
                    for d in result.diffs:
                        detail += f"\n  [{d.level}] {d.field}: {d.detail}"
                console.print(Panel(detail, title=f"Consistency: {result.tool} — {status}"))

    if as_json:
        click.echo(json.dumps(
            {"probes": results, "consistency": consistency_results},
            ensure_ascii=False,
            indent=2,
            default=str,
        ))
    else:
        console.print(probe_table)


# ------------------------------------------------------------------
# finance-data verify
# ------------------------------------------------------------------

@click.command()
@click.option("--include-pytest", is_flag=True, help="Also run pytest suite")
@click.option("--include-dashboard", is_flag=True, help="Run dashboard API alignment check")
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
def verify_cmd(include_pytest: bool, include_dashboard: bool, as_json: bool) -> None:
    """Run consistency validators and optionally pytest."""
    from finance_data.tool_specs.validators import (
        validate_probe_params_against_mcp,
        validate_service_targets,
        validate_tool_specs,
    )

    checks: dict[str, dict[str, list[str]]] = {}

    checks["tool_specs"] = validate_tool_specs()
    checks["service_targets"] = validate_service_targets()
    checks["probe_params"] = validate_probe_params_against_mcp()

    # ToolSpec ↔ ToolMeta ↔ MCP 三方一致性
    from finance_data.provider.metadata.validator import validate_toolspec_registry_consistency
    toolspec_results = validate_toolspec_registry_consistency()
    toolspec_failures = {str(r): [r.message] for r in toolspec_results if not r.passed}
    checks["toolspec_registry"] = toolspec_failures

    if include_dashboard:
        from finance_data.tool_specs.validators import validate_dashboard_tools_api_against_registry
        checks["dashboard_api"] = validate_dashboard_tools_api_against_registry()

    all_passed = all(not errors for errors in checks.values())

    pytest_ok = True
    if include_pytest:
        if not as_json:
            console.print("Running pytest...")
        ret = subprocess.run(
            [sys.executable, "-m", "pytest", "--tb=short", "-q"],
            capture_output=as_json,
        )
        pytest_ok = ret.returncode == 0
        if not as_json and not pytest_ok:
            console.print(f"[red]pytest exited with code {ret.returncode}[/red]")

    overall = all_passed and pytest_ok

    if as_json:
        output: dict = {"passed": overall, "checks": checks}
        if include_pytest:
            output["pytest"] = {"exit_code": ret.returncode, "passed": pytest_ok}
        click.echo(json.dumps(output, ensure_ascii=False, indent=2, default=str))
    else:
        for name, errors in checks.items():
            if errors:
                console.print(f"[red]FAIL[/red] {name}")
                for tool, msgs in errors.items():
                    for msg in msgs:
                        console.print(f"  {tool}: {msg}")
            else:
                console.print(f"[green]PASS[/green] {name}")

        if overall:
            console.print("\n[bold green]All checks passed.[/bold green]")
        else:
            console.print("\n[bold red]Some checks failed.[/bold red]")

    sys.exit(0 if overall else 1)
