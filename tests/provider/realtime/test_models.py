from finance_data.provider.realtime.models import RealtimeQuote


def test_realtime_quote_required_fields():
    q = RealtimeQuote(
        symbol="000001", name="平安银行", price=12.5, pct_chg=1.2,
        volume=1000000.0, amount=12500000.0,
        market_cap=None, pe=None, pb=None, turnover_rate=None,
        timestamp="2024-01-02T10:00:00",
    )
    assert q.symbol == "000001"
    assert q.price == 12.5


def test_realtime_quote_to_dict_keys():
    q = RealtimeQuote(
        symbol="000001", name="平安银行", price=12.5, pct_chg=1.2,
        volume=1000000.0, amount=12500000.0,
        market_cap=None, pe=None, pb=None, turnover_rate=None,
        timestamp="2024-01-02T10:00:00",
    )
    d = q.to_dict()
    assert set(d.keys()) == {
        "symbol", "name", "price", "pct_chg", "volume", "amount",
        "market_cap", "pe", "pb", "turnover_rate", "timestamp",
    }
