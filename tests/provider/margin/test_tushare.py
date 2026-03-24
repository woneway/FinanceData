from unittest.mock import patch
import pandas as pd
import pytest
from finance_data.provider.margin.tushare import get_margin, get_margin_detail
from finance_data.provider.types import DataResult, DataFetchError


@pytest.fixture
def mock_margin_df():
    return pd.DataFrame([{
        "trade_date": "20240301",
        "exchange_id": "SSE",
        "rzye": 7.6e11,
        "rzmre": 4.7e10,
        "rzche": 4.7e10,
        "rqye": 2.8e10,
        "rqmcl": 1.5e8,
        "rzrqye": 7.9e11,
        "rqyl": 4.4e9,
    }, {
        "trade_date": "20240301",
        "exchange_id": "SZSE",
        "rzye": 6.8e11,
        "rzmre": 5.4e10,
        "rzche": 5.2e10,
        "rqye": 1.6e10,
        "rqmcl": 9e7,
        "rzrqye": 6.9e11,
        "rqyl": 2.1e9,
    }])


def test_get_margin_returns_data(mock_margin_df):
    with patch("finance_data.provider.margin.tushare._get_pro") as mock_pro:
        mock_pro.return_value.margin.return_value = mock_margin_df
        result = get_margin(trade_date="20240301")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert len(result.data) == 2


def test_get_margin_fields(mock_margin_df):
    with patch("finance_data.provider.margin.tushare._get_pro") as mock_pro:
        mock_pro.return_value.margin.return_value = mock_margin_df
        result = get_margin(trade_date="20240301")
    row = result.data[0]
    assert row["date"] == "20240301"
    assert row["exchange"] == "上交所"
    assert row["rzye"] == 7.6e11
    assert row["rzche"] == 4.7e10


def test_get_margin_date_range(mock_margin_df):
    with patch("finance_data.provider.margin.tushare._get_pro") as mock_pro:
        mock_pro.return_value.margin.return_value = mock_margin_df
        result = get_margin(start_date="20240301", end_date="20240305")
    assert len(result.data) == 2


def test_get_margin_no_token():
    with patch("finance_data.provider.margin.tushare.os.environ.get",
               return_value=""):
        with pytest.raises(DataFetchError) as exc:
            get_margin(trade_date="20240301")
    assert exc.value.kind == "auth"


def test_get_margin_empty_raises(mock_margin_df):
    with patch("finance_data.provider.margin.tushare._get_pro") as mock_pro:
        mock_pro.return_value.margin.return_value = pd.DataFrame()
        with pytest.raises(DataFetchError) as exc:
            get_margin(trade_date="20240301")
    assert exc.value.kind == "data"


# ---- margin_detail tests ----

@pytest.fixture
def mock_margin_detail_df():
    return pd.DataFrame([{
        "trade_date": "20240301",
        "ts_code": "000001.SZ",
        "name": "平安银行",
        "rzye": 1e9,
        "rqye": 5e7,
        "rzmre": 2e8,
        "rqyl": 1e6,
        "rzche": 1e8,
        "rqchl": 5e5,
        "rqmcl": 2e6,
        "rzrqye": 1.05e9,
    }])


def test_get_margin_detail_returns_data(mock_margin_detail_df):
    with patch("finance_data.provider.margin.tushare._get_pro") as mock_pro:
        mock_pro.return_value.margin_detail.return_value = mock_margin_detail_df
        result = get_margin_detail(trade_date="20240301")
    assert isinstance(result, DataResult)
    assert result.source == "tushare"
    assert len(result.data) == 1


def test_get_margin_detail_fields(mock_margin_detail_df):
    with patch("finance_data.provider.margin.tushare._get_pro") as mock_pro:
        mock_pro.return_value.margin_detail.return_value = mock_margin_detail_df
        result = get_margin_detail(trade_date="20240301")
    row = result.data[0]
    assert row["date"] == "20240301"
    assert row["symbol"] == "000001"
    assert row["name"] == "平安银行"
    assert row["rzye"] == 1e9
    assert row["rqye"] == 5e7
    assert row["rzmre"] == 2e8
    assert row["rqyl"] == 1e6
    assert row["rzche"] == 1e8
    assert row["rqchl"] == 5e5


def test_get_margin_detail_date_range(mock_margin_detail_df):
    with patch("finance_data.provider.margin.tushare._get_pro") as mock_pro:
        mock_pro.return_value.margin_detail.return_value = mock_margin_detail_df
        result = get_margin_detail(start_date="20240301", end_date="20240305")
    assert len(result.data) == 1


def test_get_margin_detail_no_token():
    with patch("finance_data.provider.margin.tushare.os.environ.get",
               return_value=""):
        with pytest.raises(DataFetchError) as exc:
            get_margin_detail(trade_date="20240301")
    assert exc.value.kind == "auth"


def test_get_margin_detail_empty_raises(mock_margin_detail_df):
    with patch("finance_data.provider.margin.tushare._get_pro") as mock_pro:
        mock_pro.return_value.margin_detail.return_value = pd.DataFrame()
        with pytest.raises(DataFetchError) as exc:
            get_margin_detail(trade_date="20240301")
    assert exc.value.kind == "data"
