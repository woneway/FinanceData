"""雪球个股基本信息测试"""
from unittest.mock import MagicMock, patch

import pytest
import requests

from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.xueqiu.stock.history import XueqiuStockHistory


@pytest.fixture
def provider():
    return XueqiuStockHistory()


@pytest.fixture
def mock_company_response():
    """模拟 company.json 正常响应"""
    return {
        "data": {
            "company": {
                "org_short_name_cn": "平安银行",
                "org_name_cn": "平安银行股份有限公司",
                "listed_date": 1199145600000,  # 2008-01-01 00:00:00 UTC
                "provincial_name": "广东",
                "affiliate_industry": {"ind_name": "银行"},
                "established_date": 946771200000,  # 2000-01-02 00:00:00 UTC
                "main_operation_business": "银行业务",
                "org_cn_introduction": "平安银行简介",
                "chairman": "张三",
                "legal_representative": "李四",
                "general_manager": "王五",
                "secretary": "赵六",
                "reg_asset": 19405918198.0,
                "staff_num": 42000,
                "org_website": "https://bank.pingan.com",
                "email": "ir@pingan.com",
                "reg_address_cn": "深圳市",
            }
        },
        "error_code": 0,
    }


def _mock_session(json_data, status_code=200):
    session = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    session.get.return_value = resp
    return session


class TestXueqiuStockHistory:
    def test_returns_data_result(self, provider, mock_company_response):
        session = _mock_session(mock_company_response)
        with patch("finance_data.provider.xueqiu.stock.history.get_session",
                    return_value=session):
            result = provider.get_stock_info_history("000001")
        assert isinstance(result, DataResult)
        assert result.source == "xueqiu"
        assert len(result.data) == 1

    def test_fields_mapped_correctly(self, provider, mock_company_response):
        session = _mock_session(mock_company_response)
        with patch("finance_data.provider.xueqiu.stock.history.get_session",
                    return_value=session):
            result = provider.get_stock_info_history("000001")
        row = result.data[0]
        assert row["symbol"] == "000001"
        assert row["name"] == "平安银行"
        assert row["full_name"] == "平安银行股份有限公司"
        assert row["industry"] == "银行"
        assert row["area"] == "广东"
        assert row["list_date"] == "20080101"
        assert row["chairman"] == "张三"
        assert row["reg_capital"] == 19405918198.0
        assert row["staff_num"] == 42000
        assert row["website"] == "https://bank.pingan.com"
        assert row["email"] == "ir@pingan.com"
        assert row["reg_address"] == "深圳市"

    def test_sh_symbol_conversion(self, provider, mock_company_response):
        session = _mock_session(mock_company_response)
        with patch("finance_data.provider.xueqiu.stock.history.get_session",
                    return_value=session):
            provider.get_stock_info_history("600519")
        call_args = session.get.call_args
        assert call_args[1]["params"]["symbol"] == "SH600519"

    def test_network_error_raises(self, provider):
        session = MagicMock(spec=requests.Session)
        session.get.side_effect = ConnectionError("timeout")
        with patch("finance_data.provider.xueqiu.stock.history.get_session",
                    return_value=session):
            with pytest.raises(DataFetchError) as exc:
                provider.get_stock_info_history("000001")
        assert exc.value.kind == "network"
        assert exc.value.source == "xueqiu"

    def test_empty_data_retries_then_fails(self, provider):
        empty_resp = {"data": {"company": None}, "error_code": 0}
        session = _mock_session(empty_resp)
        with patch("finance_data.provider.xueqiu.stock.history.get_session",
                    return_value=session), \
             patch("finance_data.provider.xueqiu.stock.history.refresh_session",
                   return_value=session):
            with pytest.raises(DataFetchError) as exc:
                provider.get_stock_info_history("000001")
        assert exc.value.kind == "data"

    def test_none_optional_fields(self, provider):
        """reg_asset / staff_num 为 None 时返回 None"""
        data = {
            "data": {
                "company": {
                    "org_short_name_cn": "测试",
                    "org_name_cn": "测试公司",
                    "listed_date": 1199145600000,
                    "provincial_name": "",
                    "affiliate_industry": None,
                    "established_date": None,
                    "main_operation_business": None,
                    "org_cn_introduction": None,
                    "chairman": None,
                    "legal_representative": None,
                    "general_manager": None,
                    "secretary": None,
                    "reg_asset": None,
                    "staff_num": None,
                    "org_website": None,
                    "email": None,
                    "reg_address_cn": None,
                }
            }
        }
        session = _mock_session(data)
        with patch("finance_data.provider.xueqiu.stock.history.get_session",
                    return_value=session):
            result = provider.get_stock_info_history("000001")
        row = result.data[0]
        assert row["reg_capital"] is None
        assert row["staff_num"] is None
        assert row["industry"] == ""
        assert row["established_date"] == ""

    def test_http_401_raises_auth_error(self, provider):
        session = MagicMock(spec=requests.Session)
        http_error = requests.HTTPError()
        http_error.response = MagicMock()
        http_error.response.status_code = 401
        session.get.return_value.raise_for_status.side_effect = http_error
        with patch("finance_data.provider.xueqiu.stock.history.get_session",
                    return_value=session):
            with pytest.raises(DataFetchError) as exc:
                provider.get_stock_info_history("000001")
        assert exc.value.kind == "auth"
