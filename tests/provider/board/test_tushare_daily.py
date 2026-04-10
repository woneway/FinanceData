from unittest.mock import MagicMock, patch

import pandas as pd

from finance_data.interface.types import DataResult
from finance_data.provider.tushare.board.daily import TushareBoardDaily


def test_resolves_board_and_returns_daily_rows():
    index_provider = MagicMock()
    index_provider.get_board_index.return_value = DataResult(
        data=[{"board_code": "BK1283.DC", "board_name": "银行", "idx_type": "行业板块", "level": "东财一级行业"}],
        source="tushare",
        meta={},
    )
    daily_df = pd.DataFrame(
        [
            {
                "trade_date": "20260409",
                "open": 1100.0,
                "high": 1120.0,
                "low": 1090.0,
                "close": 1110.0,
                "change": 10.0,
                "pct_change": 0.91,
                "vol": 123456.0,
                "amount": 987654321.0,
                "swing": 2.5,
                "turnover_rate": 0.16,
            }
        ]
    )
    mock_pro = type("MockPro", (), {"dc_daily": lambda self, **kwargs: daily_df})()
    provider = TushareBoardDaily(index_provider=index_provider)

    with patch("finance_data.provider.tushare.board.daily.get_pro", return_value=mock_pro):
        result = provider.get_board_daily(
            board_name="银行",
            idx_type="行业板块",
            start_date="20260401",
            end_date="20260410",
        )

    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert len(result.data) == 1
    row = result.data[0]
    assert row["board_code"] == "BK1283.DC"
    assert row["board_name"] == "银行"
    assert row["close"] == 1110.0
