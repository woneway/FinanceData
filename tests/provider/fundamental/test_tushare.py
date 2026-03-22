from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from finance_data.provider.fundamental.tushare import get_financial_summary, get_dividend
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_pro():
    return MagicMock()


@pytest.fixture
def mock_income_df():
    return pd.DataFrame([{
        "end_date": "20231231", "total_revenue": 1.8e11, "n_income": 4.6e10,
    }])


@pytest.fixture
def mock_fina_df():
    return pd.DataFrame([{
        "end_date": "20231231", "roe": 11.2, "grossprofit_margin": 28.5, "n_cashflow_act": 5.2e10,
    }])


def test_get_financial_summary_returns_data_result(mock_pro, mock_income_df, mock_fina_df):
    mock_pro.income.return_value = mock_income_df
    mock_pro.fina_indicator.return_value = mock_fina_df
    with patch("finance_data.provider.fundamental.tushare._get_pro", return_value=mock_pro):
        result = get_financial_summary("000001")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert result.data[0]["roe"] == 11.2


def test_get_financial_summary_empty_raises(mock_pro):
    mock_pro.income.return_value = pd.DataFrame()
    mock_pro.fina_indicator.return_value = pd.DataFrame()
    with patch("finance_data.provider.fundamental.tushare._get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            get_financial_summary("INVALID")
    assert exc.value.kind == "data"


def test_get_dividend_returns_data_result(mock_pro):
    df = pd.DataFrame([{"ex_date": "20231215", "cash_div": 0.248, "record_date": "20231214"}])
    mock_pro.dividend.return_value = df
    with patch("finance_data.provider.fundamental.tushare._get_pro", return_value=mock_pro):
        result = get_dividend("000001")
    assert result.data[0]["per_share"] == 0.248
