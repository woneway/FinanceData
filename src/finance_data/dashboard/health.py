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
    return {
        "akshare": True,
        "tencent": True,
        "baostock": True,
        "tushare": has_tushare,
        "xueqiu": has_xueqiu,
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
        if available.get(provider.name, False):
            results.append((provider.name, provider.class_path, provider.method_name))
    return results


def _run_single_probe(
    tool_name: str,
    provider_name: str,
    class_path: str,
    method_name: str,
) -> tuple[HealthResult, Optional[list[dict]]]:
    """Execute a single probe, returning health result + raw data for comparison."""
    probe = get_tool_probe(tool_name)
    raw_params = dict(probe.default_params) if probe else {}
    params = resolve_probe_params(raw_params)

    timeout = probe.timeout_sec if probe else 30

    try:
        cls = _import_class(class_path)
        instance = cls()
        method = getattr(instance, method_name)

        # Execute with timeout to prevent a slow provider from blocking indefinitely
        start = time.monotonic()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(method, **params)
            try:
                result = future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                elapsed = (time.monotonic() - start) * 1000
                return (
                    HealthResult(
                        tool=tool_name,
                        provider=provider_name,
                        status="timeout",
                        response_time_ms=round(elapsed, 1),
                        error=f"probe exceeded {timeout}s timeout",
                    ),
                    None,
                )
        elapsed = (time.monotonic() - start) * 1000
        data = result.data if hasattr(result, "data") else []
        record_count = len(data)

        # --- Enforce ProbeSpec invariants ---
        if probe:
            # min_records check
            if probe.min_records and record_count < probe.min_records:
                return (
                    HealthResult(
                        tool=tool_name,
                        provider=provider_name,
                        status="warn",
                        response_time_ms=round(elapsed, 1),
                        record_count=record_count,
                        error=f"record_count {record_count} < min_records {probe.min_records}",
                    ),
                    data,
                )

            # required_fields check
            if probe.required_fields and data:
                missing = [
                    f for f in probe.required_fields if f not in data[0]
                ]
                if missing:
                    return (
                        HealthResult(
                            tool=tool_name,
                            provider=provider_name,
                            status="warn",
                            response_time_ms=round(elapsed, 1),
                            record_count=record_count,
                            error=f"missing required fields: {missing}",
                        ),
                        data,
                    )

        return (
            HealthResult(
                tool=tool_name,
                provider=provider_name,
                status="ok",
                response_time_ms=round(elapsed, 1),
                record_count=record_count,
            ),
            data,
        )
    except Exception as e:
        elapsed = 0.0
        err_msg = str(e)[:200]
        err_lower = err_msg.lower()
        if "timeout" in err_lower:
            status = "timeout"
        elif "无数据" in err_msg or "近期无" in err_msg:
            status = "warn"
        else:
            status = "error"
        return (
            HealthResult(
                tool=tool_name,
                provider=provider_name,
                status=status,
                response_time_ms=round(elapsed, 1),
                error=err_msg,
            ),
            None,
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

    # Group tasks by tool (preserve registry order)
    tool_tasks: OrderedDict[str, List[Tuple[str, str, str, str]]] = OrderedDict()
    for tname in tools:
        for provider_name, class_path, method_name in get_providers_for_tool(tname):
            tool_tasks.setdefault(tname, []).append(
                (tname, provider_name, class_path, method_name)
            )

    if not tool_tasks:
        return

    # Run probes sequentially — akshare uses py_mini_racer (V8 engine)
    # which crashes under concurrent thread access.
    for tname, tasks in tool_tasks.items():
        provider_data: Dict[str, list[dict]] = {}

        for t, p, c, m in tasks:
            health_result, data = _run_single_probe(t, p, c, m)
            yield health_result
            if data is not None and health_result.status == "ok":
                provider_data[p] = data

        # After all providers for this tool, run consistency check
        spec = get_tool_spec(tname)
        if len(provider_data) >= 2 and (spec is None or spec.probe.consistency_enabled):
            consistency = compare_provider_data(tname, provider_data)
            if consistency is not None:
                yield consistency
