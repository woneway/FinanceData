from unittest.mock import MagicMock, patch

from finance_data import FinanceData
from finance_data.interface.types import DataResult


def test_finance_data_board_member_passes_trade_date():
    mock_service = MagicMock()
    mock_service.get_board_member.return_value = DataResult(data=[], source="tushare", meta={})

    with patch("importlib.import_module") as import_module:
        import_module.return_value = MagicMock(board_member=mock_service)
        fd = FinanceData()
        fd.board_member_history(
            board_name="人工智能",
            idx_type="概念板块",
            trade_date="20260414",
        )

    mock_service.get_board_member.assert_called_once_with(
        board_name="人工智能",
        idx_type="概念板块",
        trade_date="20260414",
        start_date="",
        end_date="",
    )
