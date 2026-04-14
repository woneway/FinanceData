from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
from finance_data.provider.tushare.fundamental.history import TushareFinancialSummary, TushareDividend
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def mock_pro():
    return MagicMock()


@pytest.fixture
def mock_income_df():
    return pd.DataFrame([
        {"end_date": "20231231", "total_revenue": 1.8e11, "n_income": 4.6e10, "report_type": "1"},
        {"end_date": "20231231", "total_revenue": 1.7e11, "n_income": 4.5e10, "report_type": "4"},
        {"end_date": "20230930", "total_revenue": 1.2e11, "n_income": 3.6e10, "report_type": "1"},
    ])


@pytest.fixture
def mock_fina_df():
    return pd.DataFrame([{
        "end_date": "20231231", "roe_waa": 11.2, "grossprofit_margin": 28.5,
    }])


@pytest.fixture
def mock_cf_df():
    return pd.DataFrame([{
        "end_date": "20231231", "n_cashflow_act": 5.2e10,
    }])


def test_get_financial_summary_returns_data_result(mock_pro, mock_income_df, mock_fina_df, mock_cf_df):
    mock_pro.income.return_value = mock_income_df
    mock_pro.fina_indicator.return_value = mock_fina_df
    mock_pro.cashflow.return_value = mock_cf_df
    with patch("finance_data.provider.tushare.fundamental.history.get_pro", return_value=mock_pro):
        result = TushareFinancialSummary().get_financial_summary_history("000001")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert len(result.data) == 2
    assert result.data[0]["period"] == "20231231"
    assert result.data[0]["roe"] == 11.2
    assert "cash_flow" not in result.data[0]
    assert "gross_margin" not in result.data[0]


def test_get_financial_summary_empty_raises(mock_pro):
    mock_pro.income.return_value = pd.DataFrame()
    mock_pro.fina_indicator.return_value = pd.DataFrame()
    with patch("finance_data.provider.tushare.fundamental.history.get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            TushareFinancialSummary().get_financial_summary_history("INVALID")
    assert exc.value.kind == "data"


def test_get_dividend_returns_data_result(mock_pro):
    df = pd.DataFrame([{"ex_date": "20231215", "cash_div_tax": 0.285, "cash_div": 0.248, "record_date": "20231214"}])
    mock_pro.dividend.return_value = df
    with patch("finance_data.provider.tushare.fundamental.history.get_pro", return_value=mock_pro):
        result = TushareDividend().get_dividend_history("000001")
    mock_pro.dividend.assert_called_once_with(
        ts_code="000001.SZ", fields="ex_date,cash_div_tax,record_date"
    )
    assert result.data[0]["per_share"] == 0.285
