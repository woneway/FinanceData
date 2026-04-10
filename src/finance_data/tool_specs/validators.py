"""ToolSpec validation helpers."""
from __future__ import annotations

import importlib
import inspect
from typing import Any

from finance_data.tool_specs.adapters import list_tool_specs


_VALID_FRESHNESS = {"realtime", "end_of_day", "historical", "quarterly"}
_VALID_TIMING = {"T+0", "T+1_15:30", "T+1_16:00", "T+1_17:00", "next_trade_day_9:30", "quarterly"}
_VALID_SOURCE = {"akshare", "tencent", "tushare", "both", "multi"}


def validate_tool_specs() -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}
    for spec in list_tool_specs():
        tool_errors: list[str] = []
        if not spec.description:
            tool_errors.append("missing description")
        if not spec.return_fields:
            tool_errors.append("missing return_fields")
        if not spec.service.module_path or not spec.service.object_name or not spec.service.method_name:
            tool_errors.append("missing service target")
        if spec.metadata.api_name == "":
            tool_errors.append("missing api_name")
        if spec.metadata.data_freshness not in _VALID_FRESHNESS:
            tool_errors.append(f"invalid data_freshness: {spec.metadata.data_freshness!r}")
        if spec.metadata.update_timing not in _VALID_TIMING:
            tool_errors.append(f"invalid update_timing: {spec.metadata.update_timing!r}")
        if spec.metadata.source not in _VALID_SOURCE:
            tool_errors.append(f"invalid source: {spec.metadata.source!r}")
        if tool_errors:
            errors[spec.name] = tool_errors
    return errors


def validate_service_targets() -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}
    for spec in list_tool_specs():
        tool_errors: list[str] = []
        try:
            module = importlib.import_module(spec.service.module_path)
        except Exception as exc:
            tool_errors.append(f"service module import failed: {exc}")
            errors[spec.name] = tool_errors
            continue

        target_obj = getattr(module, spec.service.object_name, None)
        if target_obj is None:
            tool_errors.append(f"service object missing: {spec.service.object_name}")
        elif getattr(target_obj, spec.service.method_name, None) is None:
            tool_errors.append(f"service method missing: {spec.service.method_name}")

        if tool_errors:
            errors[spec.name] = tool_errors
    return errors


def validate_probe_params_against_mcp() -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}
    server = importlib.import_module("finance_data.mcp.server")

    for spec in list_tool_specs():
        tool_errors: list[str] = []
        fn = getattr(server, spec.name, None)
        if fn is None:
            errors[spec.name] = ["mcp function missing"]
            continue

        sig = inspect.signature(fn)
        params = sig.parameters
        for key in spec.probe.default_params:
            if key not in params:
                canonical_names = {
                    param.name
                    for param in spec.params
                    if key == param.name or key in param.aliases
                }
                if not canonical_names.intersection(params.keys()):
                    tool_errors.append(f"probe param not accepted by mcp signature: {key}")

        for param in spec.params:
            if param.required:
                accepted_names = {param.name, *param.aliases}
                if not accepted_names.intersection(spec.probe.default_params.keys()):
                    tool_errors.append(f"required param missing in probe defaults: {param.name}")

        if tool_errors:
            errors[spec.name] = tool_errors

    return errors


def validate_dashboard_tools_api_against_registry() -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}
    from fastapi.testclient import TestClient
    from finance_data.dashboard import app as dashboard_app_module

    client = TestClient(dashboard_app_module.app)
    response = client.get("/api/tools")
    response.raise_for_status()
    tools = {tool["name"]: tool for tool in response.json()}

    for spec in list_tool_specs():
        tool_errors: list[str] = []
        payload = tools.get(spec.name)
        if payload is None:
            errors[spec.name] = ["tool missing from /api/tools"]
            continue

        expected_params = [param.to_api_dict() for param in spec.params]
        if payload.get("params") != expected_params:
            tool_errors.append(
                f"params mismatch: expected={expected_params}, actual={payload.get('params')}"
            )

        expected_providers = [provider.name for provider in spec.providers]
        if payload.get("providers") != expected_providers:
            tool_errors.append(
                f"providers mismatch: expected={expected_providers}, actual={payload.get('providers')}"
            )

        expected_fields = list(spec.return_fields)
        if payload.get("return_fields") != expected_fields:
            tool_errors.append(
                f"return_fields mismatch: expected={expected_fields}, actual={payload.get('return_fields')}"
            )

        if payload.get("freshness") != spec.metadata.data_freshness:
            tool_errors.append(
                f"freshness mismatch: expected={spec.metadata.data_freshness}, actual={payload.get('freshness')}"
            )

        if payload.get("supports_history") != spec.metadata.supports_history:
            tool_errors.append(
                f"supports_history mismatch: expected={spec.metadata.supports_history}, actual={payload.get('supports_history')}"
            )

        expected_examples = list(spec.metadata.examples)
        if payload.get("examples") != expected_examples:
            tool_errors.append(
                f"examples mismatch: expected={expected_examples}, actual={payload.get('examples')}"
            )

        if tool_errors:
            errors[spec.name] = tool_errors

    extra_tools = sorted(set(tools) - {spec.name for spec in list_tool_specs()})
    if extra_tools:
        errors["/api/tools"] = [f"unexpected tools present: {extra_tools}"]

    return errors


def validate_registry_consistency() -> dict[str, Any]:
    return {
        "tool_specs": validate_tool_specs(),
        "service_targets": validate_service_targets(),
        "probe_params": validate_probe_params_against_mcp(),
        "dashboard_api": validate_dashboard_tools_api_against_registry(),
    }
