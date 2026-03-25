from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.akshare.chip.history import AkshareChipHistory
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return AkshareChipHistory()


@pytest.fixture
def mock_chip_df():
    return pd.DataFrame([{
        "日期": "2024-01-02",
        "获利比例": 55.3, "平均成本": 11.8,
        "90成本-低": 8.5, "90成本-高": 14.2, "集中度": 62.1,
    }])


def test_get_chip_distribution_returns_data_result(provider, mock_chip_df):
    with patch("finance_data.provider.akshare.chip.history.ak.stock_cyq_em",
               return_value=mock_chip_df):
        result = provider.get_chip_distribution_history("000001")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"


def test_get_chip_distribution_fields(provider, mock_chip_df):
    with patch("finance_data.provider.akshare.chip.history.ak.stock_cyq_em",
               return_value=mock_chip_df):
        result = provider.get_chip_distribution_history("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["cost_profit_ratio"] == 55.3
    assert row["avg_cost"] == 11.8
    assert row["concentration"] == 62.1


def test_get_chip_distribution_network_error(provider):
    with patch("finance_data.provider.akshare.chip.history.ak.stock_cyq_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            provider.get_chip_distribution_history("000001")
    assert exc.value.kind == "network"


def test_get_chip_distribution_empty_raises(provider):
    with patch("finance_data.provider.akshare.chip.history.ak.stock_cyq_em",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            provider.get_chip_distribution_history("INVALID")
    assert exc.value.kind == "data"
