from finance_data.provider.types import DataResult, DataFetchError


def test_data_result_basic():
    result = DataResult(
        data=[{"name": "平安银行", "code": "000001"}],
        source="akshare",
        meta={"rows": 1},
    )
    assert result.source == "akshare"
    assert len(result.data) == 1


def test_data_fetch_error_kinds():
    err = DataFetchError(source="akshare", func="get_stock_info", reason="timeout", kind="network")
    assert err.kind == "network"
    assert "akshare" in str(err)


def test_data_fetch_error_invalid_kind():
    import pytest
    with pytest.raises(ValueError):
        DataFetchError(source="akshare", func="foo", reason="x", kind="invalid_kind")
