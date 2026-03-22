from finance_data.provider.models import StockInfo


def test_stock_info_required_fields():
    info = StockInfo(symbol="000001", name="平安银行", industry="银行", list_date="19910403")
    assert info.symbol == "000001"
    assert info.name == "平安银行"
    assert info.industry == "银行"
    assert info.list_date == "19910403"


def test_stock_info_optional_fields_default_empty():
    info = StockInfo(symbol="000001", name="平安银行", industry="银行", list_date="19910403")
    assert info.area == ""
    assert info.market == ""
    assert info.full_name == ""
    assert info.established_date == ""
    assert info.main_business == ""
    assert info.introduction == ""
    assert info.chairman == ""
    assert info.legal_representative == ""
    assert info.reg_capital is None
    assert info.staff_num is None
    assert info.website == ""
    assert info.reg_address == ""
    assert info.actual_controller == ""
    assert info.ts_code == ""


def test_stock_info_all_fields():
    info = StockInfo(
        symbol="000001",
        name="平安银行",
        industry="银行",
        list_date="19910403",
        area="深圳",
        market="主板",
        full_name="平安银行股份有限公司",
        established_date="19871222",
        main_business="经有关监管机构批准的各项商业银行业务。",
        introduction="平安银行股份有限公司的主营业务...",
        chairman="谢永林",
        legal_representative="谢永林",
        reg_capital=19405918198.0,
        staff_num=41698,
        website="bank.pingan.com",
        reg_address="广东省深圳市罗湖区深南东路5047号",
        actual_controller="",
        ts_code="000001.SZ",
    )
    assert info.full_name == "平安银行股份有限公司"
    assert info.chairman == "谢永林"
    assert info.reg_capital == 19405918198.0
    assert info.staff_num == 41698
    assert info.ts_code == "000001.SZ"


def test_stock_info_to_dict_contains_all_keys():
    info = StockInfo(symbol="000001", name="平安银行", industry="银行",
                     list_date="19910403", area="深圳", market="主板",
                     full_name="平安银行股份有限公司", established_date="19871222",
                     main_business="商业银行业务", introduction="简介",
                     chairman="谢永林", legal_representative="谢永林",
                     reg_capital=19405918198.0, staff_num=41698,
                     website="bank.pingan.com", reg_address="深圳市",
                     actual_controller="", ts_code="000001.SZ")
    d = info.to_dict()
    expected_keys = {
        "symbol", "name", "industry", "list_date", "area", "market",
        "full_name", "established_date", "main_business", "introduction",
        "chairman", "legal_representative", "reg_capital", "staff_num",
        "website", "reg_address", "actual_controller", "ts_code",
    }
    assert set(d.keys()) == expected_keys
    assert d["full_name"] == "平安银行股份有限公司"
    assert d["reg_capital"] == 19405918198.0
