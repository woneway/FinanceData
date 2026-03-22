from unittest.mock import patch
import pandas as pd
import pytest

from finance_data.provider.akshare.stock import get_stock_info
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_xueqiu_df():
    return pd.DataFrame([
        {"item": "org_short_name_cn", "value": "平安银行"},
        {"item": "org_name_cn", "value": "平安银行股份有限公司"},
        {"item": "affiliate_industry", "value": {"ind_code": "BK0055", "ind_name": "银行"}},
        {"item": "listed_date", "value": 670608000000},
        {"item": "established_date", "value": 567100800000},
        {"item": "provincial_name", "value": "广东省"},
        {"item": "main_operation_business", "value": "商业银行业务"},
        {"item": "org_cn_introduction", "value": "平安银行股份有限公司简介"},
        {"item": "chairman", "value": "谢永林"},
        {"item": "legal_representative", "value": "谢永林"},
        {"item": "reg_asset", "value": 19405918198.0},
        {"item": "staff_num", "value": 41698},
        {"item": "org_website", "value": "bank.pingan.com"},
        {"item": "reg_address_cn", "value": "广东省深圳市罗湖区深南东路5047号"},
        {"item": "actual_controller", "value": ""},
    ])


def test_get_stock_info_returns_data_result(mock_xueqiu_df):
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_basic_info_xq",
               return_value=mock_xueqiu_df):
        result = get_stock_info("000001")

    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1


def test_get_stock_info_core_fields(mock_xueqiu_df):
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_basic_info_xq",
               return_value=mock_xueqiu_df):
        result = get_stock_info("000001")

    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["name"] == "平安银行"
    assert row["industry"] == "银行"
    assert row["list_date"] == "19910403"
    assert row["area"] == "广东省"


def test_get_stock_info_extended_fields(mock_xueqiu_df):
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_basic_info_xq",
               return_value=mock_xueqiu_df):
        result = get_stock_info("000001")

    row = result.data[0]
    assert row["full_name"] == "平安银行股份有限公司"
    assert row["established_date"] == "19871222"
    assert row["main_business"] == "商业银行业务"
    assert row["introduction"] == "平安银行股份有限公司简介"
    assert row["chairman"] == "谢永林"
    assert row["legal_representative"] == "谢永林"
    assert row["reg_capital"] == 19405918198.0
    assert row["staff_num"] == 41698
    assert row["website"] == "bank.pingan.com"
    assert row["reg_address"] == "广东省深圳市罗湖区深南东路5047号"
    assert row["actual_controller"] == ""


def test_get_stock_info_meta(mock_xueqiu_df):
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_basic_info_xq",
               return_value=mock_xueqiu_df):
        result = get_stock_info("000001")

    assert result.meta["symbol"] == "000001"
    assert result.meta["rows"] == 1


def test_get_stock_info_network_error():
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_basic_info_xq",
               side_effect=ConnectionError("timeout")):
        with pytest.raises(DataFetchError) as exc:
            get_stock_info("000001")

    assert exc.value.kind == "network"
    assert exc.value.source == "akshare"


def test_get_stock_info_data_error():
    with patch("finance_data.provider.akshare.stock.ak.stock_individual_basic_info_xq",
               side_effect=Exception("股票代码不存在")):
        with pytest.raises(DataFetchError) as exc:
            get_stock_info("INVALID")

    assert exc.value.kind == "data"
