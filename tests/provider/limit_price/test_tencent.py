"""腾讯 limit_price 测试"""
from unittest.mock import patch
import pytest
from finance_data.provider.tencent.limit_price import TencentLimitPrice
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return TencentLimitPrice()


@pytest.fixture
def mock_quote():
    return {
        "code": "000001", "name": "平安银行", "datetime": "20260409150000",
        "limit_up": 12.34, "limit_down": 10.10, "prev_close": 11.22, "current": 11.10,
    }


def test_returns_data_result(provider, mock_quote):
    with patch("finance_data.provider.tencent.limit_price.fetch_quote", return_value=mock_quote):
        result = provider.get_limit_price("000001")
    assert isinstance(result, DataResult)
    assert result.source == "tencent"


def test_fields_correct(provider, mock_quote):
    with patch("finance_data.provider.tencent.limit_price.fetch_quote", return_value=mock_quote):
        result = provider.get_limit_price("000001")
    row = result.data[0]
    assert row["limit_up"] == 12.34
    assert row["limit_down"] == 10.10
    assert row["prev_close"] == 11.22
    assert row["current"] == 11.10


def test_network_error(provider):
    with patch("finance_data.provider.tencent.limit_price.fetch_quote",
               side_effect=DataFetchError("tencent", "qt.gtimg.cn", "timeout", "network")):
        with pytest.raises(DataFetchError) as exc:
            provider.get_limit_price("000001")
    assert exc.value.kind == "network"
