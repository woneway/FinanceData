from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.akshare.fundamental.history import (
    AkshareFinancialSummary, AkshareDividend
)
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def mock_financial_df():
    # akshare 宽表格式：行=指标，列=报告期
    return pd.DataFrame([
        {"选项": "常用指标", "指标": "营业总收入", "20231231": 1.8e11},
        {"选项": "常用指标", "指标": "净利润", "20231231": 4.6e10},
        {"选项": "盈利能力", "指标": "净资产收益率(ROE)", "20231231": 11.2},
        {"选项": "盈利能力", "指标": "毛利率", "20231231": 28.5},
        {"选项": "现金流", "指标": "经营现金流量净额", "20231231": 5.2e10},
    ])


def test_get_financial_summary_returns_data_result(mock_financial_df):
    with patch("finance_data.provider.akshare.fundamental.history.ak.stock_financial_abstract",
               return_value=mock_financial_df):
        result = AkshareFinancialSummary().get_financial_summary_history("000001")
    assert isinstance(result, DataResult)
    assert result.source == "akshare"


def test_get_financial_summary_fields(mock_financial_df):
    with patch("finance_data.provider.akshare.fundamental.history.ak.stock_financial_abstract",
               return_value=mock_financial_df):
        result = AkshareFinancialSummary().get_financial_summary_history("000001")
    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["period"] == "20231231"
    assert row["roe"] == 11.2
    assert row["revenue"] == 1.8e11


@pytest.fixture
def mock_dividend_df():
    """同花顺 stock_fhps_detail_ths 返回格式"""
    return pd.DataFrame([{
        "A股除权除息日": "2023-12-15",
        "分红方案说明": "10派2.48元",
        "A股股权登记日": "2023-12-14",
    }])


def test_get_dividend_fields(mock_dividend_df):
    with patch("finance_data.provider.akshare.fundamental.history.ak.stock_fhps_detail_ths",
               return_value=mock_dividend_df):
        result = AkshareDividend().get_dividend_history("000001")
    row = result.data[0]
    assert row["per_share"] == 0.248
    assert row["ex_date"] == "20231215"
    assert row["record_date"] == "20231214"


def test_get_dividend_complex_plan():
    """含送转股的分红方案应正确解析派息金额"""
    df = pd.DataFrame([
        {"A股除权除息日": "2024-07-10", "分红方案说明": "10送3股转2股派5元", "A股股权登记日": "2024-07-09"},
        {"A股除权除息日": "2024-01-15", "分红方案说明": "10送5股转5股", "A股股权登记日": "2024-01-12"},
        {"A股除权除息日": pd.NaT, "分红方案说明": "不分配不转增", "A股股权登记日": pd.NaT},
    ])
    with patch("finance_data.provider.akshare.fundamental.history.ak.stock_fhps_detail_ths",
               return_value=df):
        result = AkshareDividend().get_dividend_history("000001")
    assert len(result.data) == 1
    assert result.data[0]["per_share"] == 0.5
    assert result.data[0]["ex_date"] == "20240710"


def test_get_financial_summary_network_error():
    with patch("finance_data.provider.akshare.fundamental.history.ak.stock_financial_abstract",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            AkshareFinancialSummary().get_financial_summary_history("000001")
    assert exc.value.kind == "network"


def test_get_financial_summary_empty_raises():
    with patch("finance_data.provider.akshare.fundamental.history.ak.stock_financial_abstract",
               return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            AkshareFinancialSummary().get_financial_summary_history("INVALID")
    assert exc.value.kind == "data"
