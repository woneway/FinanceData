from finance_data.dashboard.consistency import compare_provider_data


def test_compare_provider_data_supports_composite_primary_key():
    result = compare_provider_data(
        "tool_get_lhb_detail_history",
        {
            "akshare": [
                {
                    "date": "20260401",
                    "symbol": "000001",
                    "reason": "日涨幅偏离值达到7%的前5只证券",
                    "close": 10.0,
                }
            ],
            "tushare": [
                {
                    "date": "20260401",
                    "symbol": "000001",
                    "reason": "日涨幅偏离值达到7%的前5只证券",
                    "close": 10.0,
                }
            ],
        },
    )

    assert result is not None
    assert result.status == "consistent"
    assert result.diffs == []
