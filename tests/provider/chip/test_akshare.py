from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.chip.akshare import get_chip_distribution
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_chip_df():
    return pd.DataFrame([{
        "日期": "2024-01-02",
        "获利比例": 55.3, "平均成本": 11.8,
        "90成本-低": 8.5, "90成本-高": 14.2, "集中度": 62.1,
    }])


def test_get_chip_distribution_returns_data_result(mock_chip_df):
    with patch("finance_data.provider.chip.akshare.ak.stock_cyq_em",
               return_value=mock_chip_df):
        result = get_chip_distribution("000001")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"


def test_get_chip_distribution_fields(mock_chip_df):
    with patch("finance_data.provider.chip.akshare.ak.stock_cyq_em",
               return_value=mock_chip_df):
        result = get_chip_distribution("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["cost_profit_ratio"] == 55.3
    assert row["avg_cost"] == 11.8
    assert row["concentration"] == 62.1


def test_get_chip_distribution_network_error():
    with patch("finance_data.provider.chip.akshare.ak.stock_cyq_em",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_chip_distribution("000001")
    assert exc.value.kind == "network"


def test_get_chip_distribution_empty_raises():
    with patch("finance_data.provider.chip.akshare.ak.stock_cyq_em",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            get_chip_distribution("INVALID")
    assert exc.value.kind == "data"
