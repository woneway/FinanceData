from finance_data.tool_specs.validators import (
    validate_dashboard_tools_api_against_registry,
    validate_probe_params_against_mcp,
    validate_registry_consistency,
    validate_service_targets,
    validate_tool_specs,
)


def test_validate_tool_specs_passes():
    assert validate_tool_specs() == {}


def test_validate_service_targets_passes():
    assert validate_service_targets() == {}


def test_validate_probe_params_against_mcp_passes():
    assert validate_probe_params_against_mcp() == {}


def test_validate_dashboard_tools_api_against_registry_passes():
    assert validate_dashboard_tools_api_against_registry() == {}


def test_validate_registry_consistency_passes():
    result = validate_registry_consistency()
    assert result == {
        "tool_specs": {},
        "service_targets": {},
        "probe_params": {},
        "dashboard_api": {},
    }
