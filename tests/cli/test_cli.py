"""CLI command tests using click CliRunner."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from finance_data.cli import main


runner = CliRunner()


# ------------------------------------------------------------------
# tools
# ------------------------------------------------------------------

def test_tools_list():
    result = runner.invoke(main, ["tools"])
    assert result.exit_code == 0
    assert "tool_get_kline_history" in result.output


def test_tools_json():
    result = runner.invoke(main, ["tools", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    names = [t["name"] for t in data]
    assert "tool_get_kline_history" in names


def test_tools_domain_filter():
    result = runner.invoke(main, ["tools", "--domain", "kline"])
    assert result.exit_code == 0
    assert "tool_get_kline_history" in result.output


def test_tools_domain_filter_empty():
    result = runner.invoke(main, ["tools", "--domain", "nonexistent"])
    assert result.exit_code == 0
    # Table header still shows but no tool rows
    assert "tool_get_kline_history" not in result.output


# ------------------------------------------------------------------
# describe
# ------------------------------------------------------------------

def test_describe_known_tool():
    result = runner.invoke(main, ["describe", "tool_get_kline_history"])
    assert result.exit_code == 0
    assert "symbol" in result.output
    assert "akshare" in result.output


def test_describe_json():
    result = runner.invoke(main, ["describe", "tool_get_kline_history", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "tool_get_kline_history"
    assert "params" in data


def test_describe_unknown_tool():
    result = runner.invoke(main, ["describe", "nonexistent"])
    assert result.exit_code == 1
    assert "unknown tool" in result.output


# ------------------------------------------------------------------
# providers
# ------------------------------------------------------------------

def test_providers():
    result = runner.invoke(main, ["providers"])
    assert result.exit_code == 0
    assert "akshare" in result.output


def test_providers_json():
    result = runner.invoke(main, ["providers", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "akshare" in data
    assert data["akshare"] is True


# ------------------------------------------------------------------
# invoke
# ------------------------------------------------------------------

def _make_data_result(data, source="mock"):
    dr = MagicMock()
    dr.data = data
    dr.source = source
    dr.meta = {}
    return dr


def test_invoke_via_service():
    mock_result = _make_data_result(
        [{"symbol": "000001", "name": "Test", "price": 10.5, "pct_chg": 1.2, "volume": 1000, "amount": 10000}],
        source="test",
    )
    with patch("finance_data.service.realtime.realtime_quote") as mock_svc:
        mock_svc.get_realtime_quote.return_value = mock_result
        result = runner.invoke(main, ["invoke", "tool_get_realtime_quote", "-p", "symbol=000001"])
    assert result.exit_code == 0
    assert "000001" in result.output


def test_invoke_json():
    mock_result = _make_data_result(
        [{"symbol": "000001", "name": "Test", "price": 10.5, "pct_chg": 1.2, "volume": 1000, "amount": 10000}],
        source="test",
    )
    with patch("finance_data.service.realtime.realtime_quote") as mock_svc:
        mock_svc.get_realtime_quote.return_value = mock_result
        result = runner.invoke(main, ["invoke", "tool_get_realtime_quote", "-p", "symbol=000001", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["tool"] == "tool_get_realtime_quote"
    assert len(data["data"]) == 1


def test_invoke_missing_required_param():
    result = runner.invoke(main, ["invoke", "tool_get_realtime_quote"])
    assert result.exit_code == 1
    assert "missing required param" in result.output


def test_invoke_unknown_tool():
    result = runner.invoke(main, ["invoke", "nonexistent"])
    assert result.exit_code == 1
    assert "unknown tool" in result.output


def test_invoke_bad_param_format():
    result = runner.invoke(main, ["invoke", "tool_get_realtime_quote", "-p", "no_equals"])
    assert result.exit_code == 1
    assert "key=value" in result.output


def test_invoke_alias_resolves_before_required_check():
    """CLI should accept alias 'symbol' for canonical 'sector_name'."""
    mock_result = _make_data_result(
        [{"symbol": "000001", "name": "Test", "price": 10.5, "pct_chg": 1.2, "volume": 1000, "amount": 10000}],
        source="akshare",
    )
    with patch("finance_data.service.sector.sector_member") as mock_svc:
        mock_svc.get_sector_member.return_value = mock_result
        result = runner.invoke(main, ["invoke", "tool_get_sector_member", "-p", "symbol=银行"])
    assert result.exit_code == 0
    assert "000001" in result.output


# ------------------------------------------------------------------
# health
# ------------------------------------------------------------------

def test_health_unknown_tool():
    result = runner.invoke(main, ["health", "nonexistent_tool_xyz"])
    assert result.exit_code == 1
    assert "unknown tool" in result.output


# ------------------------------------------------------------------
# verify
# ------------------------------------------------------------------

def test_verify():
    result = runner.invoke(main, ["verify"])
    # Should complete without crashing; exit 0 if all validators pass
    assert result.exit_code == 0
    assert "PASS" in result.output


def test_verify_json():
    result = runner.invoke(main, ["verify", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "passed" in data
    assert "checks" in data


def test_verify_json_include_pytest_single_document():
    """--json --include-pytest must emit exactly one JSON document."""
    mock_ret = MagicMock()
    mock_ret.returncode = 0
    with patch("finance_data.cli.ops.subprocess.run", return_value=mock_ret):
        result = runner.invoke(main, ["verify", "--json", "--include-pytest"])
    # The output must be parseable as a single JSON object
    data = json.loads(result.output)
    assert "passed" in data
    assert "checks" in data
    assert "pytest" in data
    assert "exit_code" in data["pytest"]
