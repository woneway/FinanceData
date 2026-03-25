from finance_data.interface.index.realtime import IndexQuote
from finance_data.interface.index.history import IndexBar


def test_index_quote_to_dict_keys():
    q = IndexQuote(symbol="000001.SH", name="上证指数",
                   price=3100.0, pct_chg=0.5, volume=1e10,
                   amount=1e12, timestamp="2024-01-02T15:00:00")
    d = q.to_dict()
    assert set(d.keys()) == {"symbol", "name", "price", "pct_chg", "volume", "amount", "timestamp"}


def test_index_bar_to_dict_keys():
    b = IndexBar(symbol="000001.SH", date="20240102",
                 open=3090.0, high=3110.0, low=3085.0, close=3100.0,
                 volume=1e10, amount=1e12, pct_chg=0.5)
    d = b.to_dict()
    assert set(d.keys()) == {"symbol", "date", "open", "high", "low", "close", "volume", "amount", "pct_chg"}
