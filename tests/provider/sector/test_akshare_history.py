from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.akshare.sector.history import AkshareSectorHistory
from finance_data.interface.types import DataResult, DataFetchError


@pytest.fixture
def provider():
    return AkshareSectorHistory()


@pytest.fixture
def mock_df():
    return pd.DataFrame([{
        "日期": "2026-01-02",
        "开盘": 1200.0,
        "收盘": 1215.5,
        "最高": 1220.0,
        "最低": 1195.0,
        "成交量": 500000,
        "成交额": 6.1e9,
        "振幅": 2.09,
        "涨跌幅": 1.29,
        "涨跌额": 15.5,
        "换手率": 0.45,
    }])


def test_returns_data_result(provider, mock_df):
    with patch(
        "finance_data.provider.akshare.sector.history.ak.stock_board_industry_hist_em",
        return_value=mock_df,
    ):
        result = provider.get_sector_history(
            symbol="银行", start_date="20260101", end_date="20260409"
        )
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    assert len(result.data) == 1
    row = result.data[0]
    assert row["date"] == "2026-01-02"
    assert row["open"] == 1200.0
    assert row["close"] == 1215.5
    assert row["pct_chg"] == 1.29
    assert row["volume"] == 500000
    assert row["amount"] == 6.1e9


def test_empty_raises(provider):
    with patch(
        "finance_data.provider.akshare.sector.history.ak.stock_board_industry_hist_em",
        return_value=pd.DataFrame(),
    ):
        with pytest.raises(DataFetchError) as exc:
            provider.get_sector_history(
                symbol="银行", start_date="20260101", end_date="20260409"
            )
    assert exc.value.kind == "data"


def test_network_error(provider):
    with patch(
        "finance_data.provider.akshare.sector.history.ak.stock_board_industry_hist_em",
        side_effect=OSError("network error"),
    ):
        with pytest.raises(DataFetchError) as exc:
            provider.get_sector_history(
                symbol="银行", start_date="20260101", end_date="20260409"
            )
    assert exc.value.kind == "network"
