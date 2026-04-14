from unittest.mock import MagicMock, patch

from finance_data.provider.xueqiu.fundamental.history import XueqiuFinancialSummary


def test_xueqiu_financial_summary_uses_all_periods():
    session = MagicMock()
    response = MagicMock()
    response.json.return_value = {
        "data": {
            "list": [
                {
                    "report_date": 1719676800000,
                    "total_revenue": [1.2e11, 0.1],
                    "net_profit_atsopc": [3.6e10, 0.2],
                    "avg_roe": [9.1, 0.3],
                    "gross_selling_rate": [71.0, 0.0],
                }
            ]
        }
    }
    session.get.return_value = response

    with patch(
        "finance_data.provider.xueqiu.fundamental.history.get_session",
        return_value=session,
    ):
        result = XueqiuFinancialSummary().get_financial_summary_history("000001")

    session.get.assert_called_once()
    assert session.get.call_args.kwargs["params"]["type"] == "all"
    assert result.data == [
        {
            "symbol": "000001",
            "period": "20240630",
            "revenue": 1.2e11,
            "net_profit": 3.6e10,
            "roe": 9.1,
        }
    ]
