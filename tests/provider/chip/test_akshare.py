"""akshare 筹码分布测试"""
from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.akshare.chip.history import AkshareChipHistory
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return AkshareChipHistory()


@pytest.fixture
def mock_cyq_df():
    return pd.DataFrame([{
        "日期": "2025-01-02",
        "获利比例": 0.553,
        "平均成本": 11.8,
        "90成本-低": 8.5,
        "90成本-高": 14.2,
        "90集中度": 0.058,
        "70成本-低": 9.0,
        "70成本-高": 13.0,
        "70集中度": 0.041,
    }])


def test_returns_data_result(provider, mock_cyq_df):
    with patch("finance_data.provider.akshare.chip.history.ak.stock_cyq_em", return_value=mock_cyq_df):
        result = provider.get_chip_distribution_history("000001")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1


def test_fields_correct(provider, mock_cyq_df):
    with patch("finance_data.provider.akshare.chip.history.ak.stock_cyq_em", return_value=mock_cyq_df):
        result = provider.get_chip_distribution_history("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["date"] == "20250102"
    assert row["avg_cost"] == 11.8
    assert row["cost_profit_ratio"] == 0.553
    assert row["cost_90"] == 14.2
    assert row["cost_10"] == 8.5
    assert row["concentration"] == 0.058


def test_empty_raises(provider):
    with patch("finance_data.provider.akshare.chip.history.ak.stock_cyq_em", return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            provider.get_chip_distribution_history("INVALID")
    assert exc.value.kind == "data"


def test_network_error(provider):
    with patch("finance_data.provider.akshare.chip.history.ak.stock_cyq_em", side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            provider.get_chip_distribution_history("000001")
    assert exc.value.kind == "network"
