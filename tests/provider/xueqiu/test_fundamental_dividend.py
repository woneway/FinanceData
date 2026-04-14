from unittest.mock import MagicMock, patch

from finance_data.provider.xueqiu.fundamental.history import XueqiuDividend


def test_xueqiu_dividend_parses_plan_explain():
    session = MagicMock()
    response = MagicMock()
    response.json.return_value = {
        "data": {
            "items": [
                {
                    "ashare_ex_dividend_date": 1719331200000,
                    "equity_date": 1719244800000,
                    "plan_explain": "10派2.85元",
                }
            ]
        }
    }
    session.get.return_value = response

    with patch(
        "finance_data.provider.xueqiu.fundamental.history.get_session",
        return_value=session,
    ):
        result = XueqiuDividend().get_dividend_history("000001")

    assert result.source == "xueqiu"
    assert result.data == [
        {
            "symbol": "000001",
            "ex_date": "20240626",
            "per_share": 0.285,
            "record_date": "20240625",
        }
    ]
