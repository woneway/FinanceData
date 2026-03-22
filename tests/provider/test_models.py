import pytest
from finance_data.provider.models import StockInfo


def test_stock_info_required_fields():
    info = StockInfo(symbol="000001", name="平安银行", industry="银行", list_date="19910403")
    assert info.symbol == "000001"
    assert info.name == "平安银行"
    assert info.industry == "银行"
    assert info.list_date == "19910403"
    assert info.area == ""
    assert info.market == ""


def test_stock_info_optional_fields():
    info = StockInfo(symbol="000001", name="平安银行", industry="银行",
                     list_date="19910403", area="深圳", market="主板")
    assert info.area == "深圳"
    assert info.market == "主板"


def test_stock_info_to_dict():
    info = StockInfo(symbol="000001", name="平安银行", industry="银行",
                     list_date="19910403", area="深圳", market="主板")
    d = info.to_dict()
    assert d == {
        "symbol": "000001",
        "name": "平安银行",
        "industry": "银行",
        "list_date": "19910403",
        "area": "深圳",
        "market": "主板",
    }
