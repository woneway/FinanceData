from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from finance_data.provider.tushare.stock import get_stock_info
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_basic_df():
    return pd.DataFrame([{
        "ts_code": "000001.SZ",
        "name": "平安银行",
        "industry": "银行",
        "list_date": "19910403",
        "area": "深圳",
        "market": "主板",
        "act_name": "无实际控制人",
    }])


@pytest.fixture
def mock_company_df():
    return pd.DataFrame([{
        "ts_code": "000001.SZ",
        "com_name": "平安银行股份有限公司",
        "chairman": "谢永林",
        "manager": "冀光恒",
        "secretary": "周强",
        "reg_capital": 19405918198.0,
        "setup_date": "19871222",
        "province": "广东省",
        "city": "深圳市",
        "introduction": "平安银行股份有限公司简介",
        "website": "bank.pingan.com",
        "email": "pab_db@pingan.com.cn",
        "office": "广东省深圳市罗湖区深南东路5047号",
        "main_business": "商业银行业务",
        "exchange": "SZSE",
        "employees": 41698,
    }])


def _make_mock_pro(basic_df, company_df=None):
    mock_pro = MagicMock()
    mock_pro.stock_basic.return_value = basic_df
    if company_df is not None:
        mock_pro.stock_company.return_value = company_df
    else:
        mock_pro.stock_company.side_effect = Exception("company unavailable")
    return mock_pro


def test_get_stock_info_returns_data_result(mock_basic_df, mock_company_df):
    mock_pro = _make_mock_pro(mock_basic_df, mock_company_df)
    with patch("finance_data.provider.tushare.stock._get_pro", return_value=mock_pro):
        result = get_stock_info("000001")

    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert len(result.data) == 1


def test_get_stock_info_basic_fields(mock_basic_df, mock_company_df):
    mock_pro = _make_mock_pro(mock_basic_df, mock_company_df)
    with patch("finance_data.provider.tushare.stock._get_pro", return_value=mock_pro):
        result = get_stock_info("000001")

    row = result.data[0]
    assert row["symbol"] == "000001"
    assert row["name"] == "平安银行"
    assert row["industry"] == "银行"
    assert row["list_date"] == "19910403"
    assert row["area"] == "深圳"
    assert row["market"] == "主板"
    assert row["ts_code"] == "000001.SZ"
    assert row["actual_controller"] == "无实际控制人"


def test_get_stock_info_company_fields(mock_basic_df, mock_company_df):
    mock_pro = _make_mock_pro(mock_basic_df, mock_company_df)
    with patch("finance_data.provider.tushare.stock._get_pro", return_value=mock_pro):
        result = get_stock_info("000001")

    row = result.data[0]
    assert row["full_name"] == "平安银行股份有限公司"
    assert row["chairman"] == "谢永林"
    assert row["general_manager"] == "冀光恒"
    assert row["secretary"] == "周强"
    assert row["reg_capital"] == 19405918198.0
    assert row["established_date"] == "19871222"
    assert row["city"] == "深圳市"
    assert row["introduction"] == "平安银行股份有限公司简介"
    assert row["website"] == "bank.pingan.com"
    assert row["email"] == "pab_db@pingan.com.cn"
    assert row["reg_address"] == "广东省深圳市罗湖区深南东路5047号"
    assert row["main_business"] == "商业银行业务"
    assert row["exchange"] == "SZSE"
    assert row["staff_num"] == 41698


def test_get_stock_info_company_fallback(mock_basic_df):
    """stock_company 失败时仍应返回基本信息，公司字段为空。"""
    mock_pro = _make_mock_pro(mock_basic_df, company_df=None)
    with patch("finance_data.provider.tushare.stock._get_pro", return_value=mock_pro):
        result = get_stock_info("000001")

    row = result.data[0]
    assert row["name"] == "平安银行"
    assert row["full_name"] == ""
    assert row["chairman"] == ""
    assert row["reg_capital"] is None


def test_get_stock_info_meta(mock_basic_df, mock_company_df):
    mock_pro = _make_mock_pro(mock_basic_df, mock_company_df)
    with patch("finance_data.provider.tushare.stock._get_pro", return_value=mock_pro):
        result = get_stock_info("000001")

    assert result.meta["symbol"] == "000001"
    assert result.meta["rows"] == 1


def test_get_stock_info_empty_result_raises_data_fetch_error():
    mock_pro = _make_mock_pro(pd.DataFrame())
    with patch("finance_data.provider.tushare.stock._get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            get_stock_info("INVALID")

    assert exc.value.kind == "data"
    assert exc.value.source == "tushare"


def test_get_stock_info_auth_error():
    mock_pro = MagicMock()
    mock_pro.stock_basic.side_effect = Exception("无权限访问该接口")

    with patch("finance_data.provider.tushare.stock._get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            get_stock_info("000001")

    assert exc.value.kind == "auth"


def test_get_stock_info_network_error():
    mock_pro = MagicMock()
    mock_pro.stock_basic.side_effect = ConnectionError("timeout")

    with patch("finance_data.provider.tushare.stock._get_pro", return_value=mock_pro):
        with pytest.raises(DataFetchError) as exc:
            get_stock_info("000001")

    assert exc.value.kind == "network"


def test_get_stock_info_missing_token():
    with patch("finance_data.provider.tushare.stock._get_pro",
               side_effect=DataFetchError("tushare", "init", "TUSHARE_TOKEN 未设置", "auth")):
        with pytest.raises(DataFetchError) as exc:
            get_stock_info("000001")

    assert exc.value.kind == "auth"
