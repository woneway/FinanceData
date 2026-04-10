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
    probe_table.add_column("Layer")
    probe_table.add_column("Status")
    probe_table.add_column("Time (ms)", justify="right")
    probe_table.add_column("Records", justify="right")
    probe_table.add_column("Error Kind")
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
                    result.layer,
                    status_map.get(result.status, result.status),
                    str(result.response_time_ms),
                    str(result.record_count),
                    result.error_kind or "",
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
@click.option("--include-smoke", is_flag=True, help="Run smoke tests (requires network)")
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
def verify_cmd(
    include_pytest: bool,
    include_dashboard: bool,
    include_smoke: bool,
    as_json: bool,
) -> None:
    """Run consistency validators and optionally pytest / smoke tests."""
    from finance_data.verify import print_report, run_verify

    report = run_verify(
        include_smoke=include_smoke,
        include_dashboard=include_dashboard,
    )

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

    overall = report.passed and pytest_ok

    if as_json:
        output = json.loads(report.model_dump_json())
        output["passed"] = overall
        if include_pytest:
            output["pytest"] = {"exit_code": ret.returncode, "passed": pytest_ok}
        click.echo(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_report(report)

    sys.exit(0 if overall else 1)
