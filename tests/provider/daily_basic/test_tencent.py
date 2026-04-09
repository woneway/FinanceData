"""腾讯 daily_basic 测试"""
from unittest.mock import patch
import pytest
from finance_data.provider.tencent.daily_basic import TencentDailyBasic
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return TencentDailyBasic()


@pytest.fixture
def mock_quote():
    return {
        "code": "000001", "name": "平安银行", "datetime": "20260409150000",
        "pe": 5.05, "pb": 0.48, "market_cap": 2154e8, "circ_market_cap": 2154e8,
        "turnover_rate": 0.17, "volume_ratio": 1.16,
    }


def test_returns_data_result(provider, mock_quote):
    with patch("finance_data.provider.tencent.daily_basic.fetch_quote", return_value=mock_quote):
        result = provider.get_daily_basic("000001")
    assert isinstance(result, DataResult)
    assert result.source == "tencent"
    assert len(result.data) == 1


def test_fields_correct(provider, mock_quote):
    with patch("finance_data.provider.tencent.daily_basic.fetch_quote", return_value=mock_quote):
        result = provider.get_daily_basic("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["pe"] == 5.05
    assert row["pb"] == 0.48
    assert row["turnover_rate"] == 0.17
    assert row["volume_ratio"] == 1.16


def test_network_error(provider):
    with patch("finance_data.provider.tencent.daily_basic.fetch_quote",
               side_effect=DataFetchError("tencent", "qt.gtimg.cn", "timeout", "network")):
        with pytest.raises(DataFetchError) as exc:
            provider.get_daily_basic("000001")
    assert exc.value.kind == "network"
