from finance_data.provider.metadata.registry import TOOL_REGISTRY
from finance_data.tool_specs import (
    get_tool_probe,
    get_tool_service_target,
    get_tool_spec,
    list_tool_specs,
    normalize_tool_params,
    validate_tool_specs,
)


def test_toolspec_registry_matches_metadata_registry():
    spec_names = [spec.name for spec in list_tool_specs()]
    assert spec_names == list(TOOL_REGISTRY.keys())


def test_realtime_quote_toolspec_has_expected_service_and_providers():
    spec = get_tool_spec("tool_get_realtime_quote")
    assert spec is not None
    assert spec.service.module_path == "finance_data.service.realtime"
    assert spec.service.object_name == "realtime_quote"
    assert spec.service.method_name == "get_realtime_quote"
    assert [provider.name for provider in spec.providers] == ["tushare", "xueqiu"]


def test_sector_history_toolspec_probe_and_aliases():
    probe = get_tool_probe("tool_get_sector_history")
    assert probe is not None
    assert probe.default_params["symbol"] == "银行"

    normalized = normalize_tool_params(
        "tool_get_sector_history",
        {"sector_name": "半导体", "start_date": "20240101"},
    )
    assert normalized["symbol"] == "半导体"
    assert "sector_name" not in normalized


def test_get_tool_service_target_returns_target():
    target = get_tool_service_target("tool_get_suspend")
    assert target is not None
    assert target.module_path == "finance_data.service.suspend"
    assert target.object_name == "suspend"
    assert target.method_name == "get_suspend_history"


def test_validate_tool_specs_passes():
    assert validate_tool_specs() == {}
