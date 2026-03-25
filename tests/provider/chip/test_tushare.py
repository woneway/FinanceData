from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from finance_data.provider.tushare.chip.history import TushareChipHistory
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return TushareChipHistory()


@pytest.fixture
def mock_pro():
    return MagicMock()


@pytest.fixture
def mock_cyq_df():
    return pd.DataFrame([{
        "ts_code": "000001.SZ",
        "trade_date": "20240102",
        "weight_avg": 11.8,
        "winner_rate": 55.3,
        "cost_5pct": 8.5,
        "cost_95pct": 14.2,
    }])


def test_get_chip_distribution_returns_data_result(provider, mock_pro, mock_cyq_df):
    mock_pro.cyq_perf.return_value = mock_cyq_df
    with patch("finance_data.provider.tushare.chip.history.get_pro", return_value=mock_pro):
        result = provider.get_chip_distribution_history("000001")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"


def test_get_chip_distribution_fields(provider, mock_pro, mock_cyq_df):
    mock_pro.cyq_perf.return_value = mock_cyq_df
    with patch("finance_data.provider.tushare.chip.history.get_pro", return_value=mock_pro):
        result = provider.get_chip_distribution_history("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["avg_cost"] == 11.8
    assert row["cost_profit_ratio"] == 55.3
    assert row["cost_90"] == 14.2
    assert row["cost_10"] == 8.5
    assert row["concentration"] is None


def test_get_chip_distribution_empty_raises(provider, mock_pro):
    mock_pro.cyq_perf.return_value = pd.DataFrame()
    with patch("finance_data.provider.tushare.chip.history.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            provider.get_chip_distribution_history("INVALID")
    assert exc.value.kind == "data"


def test_get_chip_distribution_auth_error(provider, mock_pro):
    mock_pro.cyq_perf.side_effect = Exception("token invalid")
    with patch("finance_data.provider.tushare.chip.history.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            provider.get_chip_distribution_history("000001")
    assert exc.value.kind == "auth"
