from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from finance_data.interface.types import DataFetchError, DataResult
from finance_data.provider.tushare.board.member import TushareBoardMember


@pytest.fixture
def member_df():
    return pd.DataFrame(
        [
            {"trade_date": "20260409", "ts_code": "BK1283.DC", "con_code": "600000.SH", "name": "浦发银行"},
            {"trade_date": "20260409", "ts_code": "BK1283.DC", "con_code": "601398.SH", "name": "工商银行"},
        ]
    )


def test_resolves_board_and_returns_members(member_df):
    index_provider = MagicMock()
    index_provider.get_board_index.return_value = DataResult(
        data=[{"board_code": "BK1283.DC", "board_name": "银行", "idx_type": "行业板块"}],
        source="tushare",
        meta={},
    )
    mock_pro = type("MockPro", (), {"dc_member": lambda self, **kwargs: member_df})()
    provider = TushareBoardMember(index_provider=index_provider)

    with patch("finance_data.provider.tushare.board.member.get_pro", return_value=mock_pro):
        result = provider.get_board_member(board_name="银行", idx_type="行业板块")

    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert len(result.data) == 2
    assert result.data[0]["board_code"] == "BK1283.DC"
    assert result.data[0]["symbol"] == "600000.SH"
    index_provider.get_board_index.assert_called_once_with(
        idx_type="行业板块",
        trade_date="",
        start_date="",
        end_date="",
    )


def test_resolves_board_with_trade_date(member_df):
    index_provider = MagicMock()
    index_provider.get_board_index.return_value = DataResult(
        data=[{"board_code": "BK0800.DC", "board_name": "人工智能", "idx_type": "概念板块"}],
        source="tushare",
        meta={},
    )
    mock_pro = type("MockPro", (), {"dc_member": lambda self, **kwargs: member_df})()
    provider = TushareBoardMember(index_provider=index_provider)

    with patch("finance_data.provider.tushare.board.member.get_pro", return_value=mock_pro):
        provider.get_board_member(
            board_name="人工智能",
            idx_type="概念板块",
            trade_date="20260414",
        )

    index_provider.get_board_index.assert_called_once_with(
        idx_type="概念板块",
        trade_date="20260414",
        start_date="",
        end_date="",
    )


def test_missing_board_raises():
    index_provider = MagicMock()
    index_provider.get_board_index.return_value = DataResult(data=[], source="tushare", meta={})
    provider = TushareBoardMember(index_provider=index_provider)
    with pytest.raises(DataFetchError) as exc:
        provider.get_board_member(board_name="银行", idx_type="行业板块")
    assert exc.value.kind == "data"
