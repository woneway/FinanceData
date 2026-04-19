"""Health probe logic for dashboard"""
from __future__ import annotations

import concurrent.futures
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Generator, List, Optional, Tuple

from finance_data.dashboard.consistency import compare_provider_data
from finance_data.dashboard.models import ConsistencyResult, HealthResult
from finance_data.interface.types import DataFetchError
from finance_data.tool_specs import get_tool_probe, get_tool_spec, list_tool_specs

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Probe date resolution
# ------------------------------------------------------------------

_RECENT_RE = re.compile(r"^\$RECENT(?:-(\d+))?$")


def _recent_trade_date() -> datetime:
    """Return the most recent likely trading day (skip weekends).

    Uses a simple heuristic — no calendar service call to avoid circular
    dependencies during health probing.
    """
    now = datetime.now()
    # Use yesterday for EOD tools whose data may not be ready today
    d = now - timedelta(days=1)
    # Skip weekends
    while d.weekday() >= 5:  # 5=Sat, 6=Sun
        d -= timedelta(days=1)
    return d


def resolve_probe_params(params: dict[str, Any]) -> dict[str, Any]:
    """Replace ``$RECENT`` / ``$RECENT-N`` placeholders with YYYYMMDD dates."""
    resolved = {}
    base = _recent_trade_date()
    for key, value in params.items():
        if isinstance(value, str):
            m = _RECENT_RE.match(value)
            if m:
                offset_days = int(m.group(1)) if m.group(1) else 0
                resolved[key] = (base - timedelta(days=offset_days)).strftime("%Y%m%d")
                continue
        resolved[key] = value
    return resolved


def _get_available_providers() -> Dict[str, bool]:
    """Check which providers are available"""
    try:
        from finance_data.provider.tushare.client import is_token_valid
        has_tushare = is_token_valid()
    except Exception:
        has_tushare = False
    try:
        from finance_data.provider.xueqiu.client import has_login_cookie
        has_xueqiu = has_login_cookie()
    except Exception:
        has_xueqiu = False
    from finance_data.config import has_tushare_stock_minute_permission
    has_tushare_stock_minute = has_tushare and has_tushare_stock_minute_permission()
    return {
        "akshare": True,
        "tencent": True,
        "baostock": True,
        "tushare": has_tushare,
        "tushare_token": has_tushare,
        "tushare_stock_minute_permission": has_tushare_stock_minute,
        "xueqiu": has_xueqiu,
        "xueqiu_cookie": has_xueqiu,
    }


def _import_class(dotted_path: str):
    """Import a class from 'module.path:ClassName'"""
    module_path, class_name = dotted_path.rsplit(":", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def get_providers_for_tool(tool_name: str) -> List[Tuple[str, str, str]]:
    """Return (provider_name, class_path, method_name) tuples for a tool.

    Only includes providers whose credentials are available.
    """
    spec = get_tool_spec(tool_name)
    if spec is None:
        return []

    available = _get_available_providers()
    results = []
    for provider in spec.providers:
        condition = provider.available_if or provider.name
        if available.get(condition, available.get(provider.name, False)):
            results.append((provider.name, provider.class_path, provider.method_name))
    return results


def _check_schema(tool_name: str, data: list[dict]) -> bool | None:
    """Check if first row contains all return_fields from ToolSpec.

    Returns None if data is empty or tool has no return_fields.
    """
    if not data:
        return None
    spec = get_tool_spec(tool_name)
    if spec is None or not spec.return_fields:
        return None
    return all(f in data[0] for f in spec.return_fields)


def _run_single_probe(
    tool_name: str,
    provider_name: str,
    class_path: str,
    method_name: str,
) -> tuple[HealthResult, Optional[list[dict]]]:
    """Execute a single provider probe, returning health result + raw data."""
    probe = get_tool_probe(tool_name)
    raw_params = dict(probe.default_params) if probe else {}
    params = resolve_probe_params(raw_params)
    timeout = probe.timeout_sec if probe else 30

    try:
        cls = _import_class(class_path)
        instance = cls()
        method = getattr(instance, method_name)

        start = time.monotonic()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(method, **params)
            try:
                result = future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                elapsed = (time.monotonic() - start) * 1000
                return (
                    HealthResult(
                        tool=tool_name, provider=provider_name,
                        status="timeout", response_time_ms=round(elapsed, 1),
                        error=f"probe exceeded {timeout}s timeout",
                        error_kind="timeout", layer="provider",
                    ),
                    None,
                )
        elapsed = (time.monotonic() - start) * 1000
        data = result.data if hasattr(result, "data") else []
        record_count = len(data)

        # --- Enforce ProbeSpec invariants ---
        if probe:
            if probe.min_records and record_count < probe.min_records:
                return (
                    HealthResult(
                        tool=tool_name, provider=provider_name,
                        status="warn", response_time_ms=round(elapsed, 1),
                        record_count=record_count,
                        error=f"record_count {record_count} < min_records {probe.min_records}",
                        error_kind="data", layer="provider",
                    ),
                    data,
                )

            if probe.required_fields and data:
                missing = [f for f in probe.required_fields if f not in data[0]]
                if missing:
                    return (
                        HealthResult(
                            tool=tool_name, provider=provider_name,
                            status="warn", response_time_ms=round(elapsed, 1),
                            record_count=record_count,
                            error=f"missing required fields: {missing}",
                            error_kind="data", layer="provider",
                        ),
                        data,
                    )

        # Schema check against ToolSpec.return_fields
        schema_ok = _check_schema(tool_name, data)
        if schema_ok is False:
            spec = get_tool_spec(tool_name)
            schema_missing = [f for f in spec.return_fields if f not in data[0]]
            return (
                HealthResult(
                    tool=tool_name, provider=provider_name,
                    status="warn", response_time_ms=round(elapsed, 1),
                    record_count=record_count,
                    error=f"schema mismatch: missing return_fields {schema_missing}",
                    error_kind="schema", schema_ok=False, layer="provider",
                ),
                data,
            )

        return (
            HealthResult(
                tool=tool_name, provider=provider_name,
                status="ok", response_time_ms=round(elapsed, 1),
                record_count=record_count,
                schema_ok=schema_ok, layer="provider",
            ),
            data,
        )
    except DataFetchError as e:
        elapsed = (time.monotonic() - start) * 1000 if "start" in dir() else 0.0
        status = "warn" if e.kind == "data" else "error"
        return (
            HealthResult(
                tool=tool_name, provider=provider_name,
                status=status, response_time_ms=round(elapsed, 1),
                error=str(e)[:200],
                error_kind=e.kind, layer="provider",
            ),
            None,
        )
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000 if "start" in dir() else 0.0
        err_msg = str(e)[:200]
        return (
            HealthResult(
                tool=tool_name, provider=provider_name,
                status="error", response_time_ms=round(elapsed, 1),
                error=err_msg, layer="provider",
            ),
            None,
        )


def _run_service_probe(tool_name: str) -> HealthResult:
    """Execute a probe through the service dispatcher to verify fallback works."""
    import importlib

    probe = get_tool_probe(tool_name)
    spec = get_tool_spec(tool_name)
    if spec is None:
        return HealthResult(
            tool=tool_name, provider="service", status="error",
            error="no ToolSpec found", layer="service",
        )

    raw_params = dict(probe.default_params) if probe else {}
    params = resolve_probe_params(raw_params)
    timeout = probe.timeout_sec if probe else 30

    target = spec.service
    start = time.monotonic()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            def _call():
                mod = importlib.import_module(target.module_path)
                dispatcher = getattr(mod, target.object_name)
                method = getattr(dispatcher, target.method_name)
                return method(**params)

            future = executor.submit(_call)
            try:
                result = future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                elapsed = (time.monotonic() - start) * 1000
                return HealthResult(
                    tool=tool_name, provider="service", status="timeout",
                    response_time_ms=round(elapsed, 1),
                    error=f"service probe exceeded {timeout}s timeout",
                    error_kind="timeout", layer="service",
                )

        elapsed = (time.monotonic() - start) * 1000
        data = result.data if hasattr(result, "data") else []
        source = result.source if hasattr(result, "source") else "service"
        schema_ok = _check_schema(tool_name, data)

        return HealthResult(
            tool=tool_name, provider=source, status="ok",
            response_time_ms=round(elapsed, 1),
            record_count=len(data),
            schema_ok=schema_ok, layer="service",
        )
    except DataFetchError as e:
        elapsed = (time.monotonic() - start) * 1000
        status = "warn" if e.kind == "data" else "error"
        return HealthResult(
            tool=tool_name, provider="service", status=status,
            response_time_ms=round(elapsed, 1),
            error=str(e)[:200],
            error_kind=e.kind, layer="service",
        )
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return HealthResult(
            tool=tool_name, provider="service", status="error",
            response_time_ms=round(elapsed, 1),
            error=str(e)[:200], layer="service",
        )


def run_probes(
    tool_name: Optional[str] = None,
) -> Generator[HealthResult | ConsistencyResult, None, None]:
    """Run health probes and yield results as they complete.

    After all providers for a tool finish, yields a ConsistencyResult
    if 2+ providers returned data successfully.

    Args:
        tool_name: If given, only probe this specific tool. Otherwise probe all.
    """
    from collections import OrderedDict

    if tool_name:
        spec = get_tool_spec(tool_name)
        tools = OrderedDict([(tool_name, spec)]) if spec is not None else OrderedDict()
    else:
        tools = OrderedDict((spec.name, spec) for spec in list_tool_specs())

    # Group provider tasks by tool (preserve registry order)
    tool_tasks: OrderedDict[str, List[Tuple[str, str, str, str]]] = OrderedDict()
    for tname in tools:
        for provider_name, class_path, method_name in get_providers_for_tool(tname):
            tool_tasks.setdefault(tname, []).append(
                (tname, provider_name, class_path, method_name)
            )

    if not tools:
        return

    # Run probes sequentially — akshare uses py_mini_racer (V8 engine)
    # which crashes under concurrent thread access.
    for tname in tools:
        provider_data: Dict[str, list[dict]] = {}

        # Provider probes (only if credentials available)
        for t, p, c, m in tool_tasks.get(tname, []):
            health_result, data = _run_single_probe(t, p, c, m)
            yield health_result
            if data is not None and health_result.status == "ok":
                provider_data[p] = data

        # Service-level probe (always, even if no provider probes ran)
        yield _run_service_probe(tname)

        # After all providers for this tool, run consistency check
        spec = get_tool_spec(tname)
        if len(provider_data) >= 2 and (spec is None or spec.probe.consistency_enabled):
            consistency = compare_provider_data(tname, provider_data)
            if consistency is not None:
                yield consistency
