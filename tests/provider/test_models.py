from finance_data.interface.stock.history import StockInfo


def test_stock_info_required_fields():
    info = StockInfo(symbol="000001", name="平安银行", industry="银行", list_date="19910403")
    assert info.symbol == "000001"
    assert info.name == "平安银行"
    assert info.industry == "银行"
    assert info.list_date == "19910403"


def test_stock_info_optional_fields_default_empty():
    info = StockInfo(symbol="000001", name="平安银行", industry="银行", list_date="19910403")
    assert info.full_name == ""
    assert info.established_date == ""
    assert info.chairman == ""
    assert info.general_manager == ""
    assert info.secretary == ""
    assert info.reg_capital is None
    assert info.staff_num is None
    assert info.website == ""
    assert info.email == ""
    assert info.exchange == ""


def test_stock_info_all_fields():
    info = StockInfo(
        symbol="000001", name="平安银行", industry="银行", list_date="19910403",
        full_name="平安银行股份有限公司",
        established_date="19871222",
        chairman="谢永林",
        general_manager="冀光恒", secretary="周强",
        reg_capital=19405918198.0, staff_num=41698,
        website="bank.pingan.com", email="pab_db@pingan.com.cn",
        exchange="SZSE",
    )
    assert info.general_manager == "冀光恒"
    assert info.secretary == "周强"
    assert info.email == "pab_db@pingan.com.cn"
    assert info.exchange == "SZSE"


def test_stock_info_to_dict_contains_all_keys():
    info = StockInfo(
        symbol="000001", name="平安银行", industry="银行", list_date="19910403",
        full_name="平安银行股份有限公司",
        established_date="19871222",
        chairman="谢永林",
        general_manager="冀光恒", secretary="周强",
        reg_capital=19405918198.0, staff_num=41698,
        website="bank.pingan.com", email="pab_db@pingan.com.cn",
        exchange="SZSE",
    )
    d = info.to_dict()
    expected_keys = {
        "symbol", "name", "industry", "list_date",
        "full_name", "established_date",
        "chairman", "general_manager", "secretary",
        "reg_capital", "staff_num",
        "website", "email",
        "exchange",
    }
    assert set(d.keys()) == expected_keys
    assert d["general_manager"] == "冀光恒"
    assert d["exchange"] == "SZSE"
