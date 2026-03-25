from finance_data.interface.kline.history import KlineBar


def test_kline_bar_required_fields():
    bar = KlineBar(
        symbol="000001", date="20240101", period="daily",
        open=10.0, high=11.0, low=9.5, close=10.5,
        volume=100000.0, amount=1050000.0, pct_chg=1.5, adj="qfq",
    )
    assert bar.symbol == "000001"
    assert bar.period == "daily"
    assert bar.close == 10.5


def test_kline_bar_to_dict_keys():
    bar = KlineBar(
        symbol="000001", date="20240101", period="daily",
        open=10.0, high=11.0, low=9.5, close=10.5,
        volume=100000.0, amount=1050000.0, pct_chg=1.5, adj="qfq",
    )
    d = bar.to_dict()
    expected = {"symbol", "date", "period", "open", "high", "low", "close",
                "volume", "amount", "pct_chg", "adj"}
    assert set(d.keys()) == expected
