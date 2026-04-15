"""Tool listing, description, invocation, and provider commands."""
from __future__ import annotations

import json
import sys
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from finance_data.tool_specs import (
    get_tool_spec,
    invoke_tool_spec,
    list_tool_specs,
)
from finance_data.tool_specs.invoke import ToolInvokeError

console = Console()


# ------------------------------------------------------------------
# finance-data tools
# ------------------------------------------------------------------

@click.command()
@click.option("--domain", default=None, help="Filter by domain")
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
def tools_cmd(domain: str | None, as_json: bool) -> None:
    """List all registered tools."""
    specs = list_tool_specs()
    if domain:
        specs = [s for s in specs if s.domain == domain]

    if as_json:
        rows = [
            {
                "name": s.name,
                "domain": s.domain,
                "description": s.description,
                "providers": [p.name for p in s.providers],
            }
            for s in specs
        ]
        click.echo(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"Tools ({len(specs)})")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Domain")
    table.add_column("Description")
    table.add_column("Providers")
    for s in specs:
        providers = ", ".join(p.name for p in s.providers)
        table.add_row(s.name, s.domain, s.description, providers)
    console.print(table)


# ------------------------------------------------------------------
# finance-data describe
# ------------------------------------------------------------------

def _spec_to_dict(spec) -> dict[str, Any]:
    """Serialize a ToolSpec to a plain dict for JSON output."""
    return {
        "name": spec.name,
        "description": spec.description,
        "domain": spec.domain,
        "params": [
            {
                "name": p.name,
                "required": p.required,
                "default": p.default,
                "description": p.description,
                "example": p.example,
                "aliases": list(p.aliases),
                "choices": [{"value": c.value, "label": c.label} for c in p.choices],
            }
            for p in spec.params
        ],
        "return_fields": list(spec.return_fields),
        "service": {
            "module": spec.service.module_path,
            "object": spec.service.object_name,
            "method": spec.service.method_name,
        },
        "providers": [
            {"name": p.name, "class_path": p.class_path, "available_if": p.available_if}
            for p in spec.providers
        ],
        "probe": {
            "default_params": spec.probe.default_params,
            "timeout_sec": spec.probe.timeout_sec,
            "min_records": spec.probe.min_records,
            "required_fields": list(spec.probe.required_fields),
            "consistency_enabled": spec.probe.consistency_enabled,
        },
        "metadata": {
            "entity": spec.metadata.entity,
            "scope": spec.metadata.scope,
            "data_freshness": spec.metadata.data_freshness,
            "update_timing": spec.metadata.update_timing,
            "supports_history": spec.metadata.supports_history,
            "history_start": spec.metadata.history_start,
            "cache_ttl": spec.metadata.cache_ttl,
            "source": spec.metadata.source,
            "source_priority": spec.metadata.source_priority,
            "api_name": spec.metadata.api_name,
            "limitations": list(spec.metadata.limitations),
            "primary_key": spec.metadata.primary_key,
        },
    }


@click.command()
@click.argument("tool")
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
def describe_cmd(tool: str, as_json: bool) -> None:
    """Show detailed info for a single tool."""
    spec = get_tool_spec(tool)
    if spec is None:
        click.echo(f"Error: unknown tool '{tool}'", err=True)
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(_spec_to_dict(spec), ensure_ascii=False, indent=2))
        return

    # Params table
    if spec.params:
        pt = Table(title="Params")
        pt.add_column("Name", style="cyan")
        pt.add_column("Required")
        pt.add_column("Default")
        pt.add_column("Description")
        pt.add_column("Choices")
        pt.add_column("Example")
        for p in spec.params:
            choices = ", ".join(f"{c.value}={c.label}" for c in p.choices)
            pt.add_row(
                p.name,
                "yes" if p.required else "no",
                str(p.default) if p.default is not None else "",
                p.description,
                choices,
                str(p.example) if p.example is not None else "",
            )
        console.print(pt)

    # Return fields
    console.print(Panel(", ".join(spec.return_fields), title="Return Fields"))

    # Service target
    svc = spec.service
    console.print(Panel(f"{svc.module_path}.{svc.object_name}.{svc.method_name}", title="Service Target"))

    # Providers
    prov_t = Table(title="Providers")
    prov_t.add_column("Name", style="cyan")
    prov_t.add_column("Class")
    prov_t.add_column("Condition")
    for p in spec.providers:
        prov_t.add_row(p.name, p.class_path, p.available_if or "always")
    console.print(prov_t)

    # Metadata
    m = spec.metadata
    meta_lines = (
        f"entity={m.entity}  scope={m.scope}  freshness={m.data_freshness}\n"
        f"update_timing={m.update_timing}  supports_history={m.supports_history}\n"
        f"source={m.source}  priority={m.source_priority}  api={m.api_name}\n"
        f"primary_key={m.primary_key}  cache_ttl={m.cache_ttl}"
    )
    console.print(Panel(meta_lines, title="Metadata"))

    if m.limitations:
        console.print(Panel("\n".join(f"- {l}" for l in m.limitations), title="Limitations"))


# ------------------------------------------------------------------
# finance-data invoke
# ------------------------------------------------------------------

@click.command()
@click.argument("tool")
@click.option("--param", "-p", multiple=True, help="key=value parameter")
@click.option("--provider", default=None, help="Direct provider (bypass dispatcher)")
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
def invoke_cmd(tool: str, param: tuple[str, ...], provider: str | None, as_json: bool) -> None:
    """Invoke a tool via service dispatcher or direct provider."""
    spec = get_tool_spec(tool)
    if spec is None:
        click.echo(f"Error: unknown tool '{tool}'", err=True)
        sys.exit(1)

    # Parse params
    params: dict[str, Any] = {}
    for kv in param:
        if "=" not in kv:
            click.echo(f"Error: param must be key=value, got '{kv}'", err=True)
            sys.exit(1)
        k, v = kv.split("=", 1)
        params[k] = v

    try:
        invoked = invoke_tool_spec(tool, params, provider=provider)
        result = invoked.result
        elapsed = invoked.response_time_ms

        if as_json:
            click.echo(json.dumps(
                {
                    "tool": tool,
                    "provider": invoked.provider,
                    "response_time_ms": elapsed,
                    "data": result.data,
                    "source": result.source,
                    "meta": result.meta,
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            ))
            return

        console.print(f"[green]OK[/green] source={result.source} time={elapsed}ms records={len(result.data)}")
        if result.data:
            table = Table()
            fields = list(spec.return_fields)
            # Use return_fields as columns, fall back to data keys
            if result.data and not all(f in result.data[0] for f in fields):
                fields = list(result.data[0].keys())
            for f in fields:
                table.add_column(f)
            for row in result.data[:50]:
                table.add_row(*(str(row.get(f, "")) for f in fields))
            if len(result.data) > 50:
                console.print(f"  ... showing 50 of {len(result.data)} records")
            console.print(table)

    except (ToolInvokeError, Exception) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# ------------------------------------------------------------------
# finance-data providers
# ------------------------------------------------------------------

@click.command()
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
def providers_cmd(as_json: bool) -> None:
    """Show provider availability status."""
    from finance_data.dashboard.health import _get_available_providers

    available = _get_available_providers()

    if as_json:
        click.echo(json.dumps(available, ensure_ascii=False, indent=2))
        return

    table = Table(title="Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Available")
    for name, ok in available.items():
        status = "[green]yes[/green]" if ok else "[red]no[/red]"
        table.add_row(name, status)
    console.print(table)
