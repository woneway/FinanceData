"""停牌信息 - akshare 实现（东财源，需绕过代理）"""
import akshare as ak

from finance_data.provider.akshare._proxy import ensure_eastmoney_no_proxy

ensure_eastmoney_no_proxy()

from finance_data.interface.suspend.history import SuspendInfo
from finance_data.interface.types import DataResult, DataFetchError

_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def _str(val) -> str:
    if val is None:
        return ""
    try:
        if float(val) != float(val):
            return ""
    except (TypeError, ValueError):
        pass
    return str(val)


def _date(val) -> str:
    if val is None:
        return ""
    s = str(val).replace("-", "")[:8]
    return s if s.isdigit() else ""


class AkshareSuspend:
    """停牌信息 - 东财源（stock_tfp_em）"""

    def get_suspend_history(self, date: str) -> DataResult:
        try:
            df = ak.stock_tfp_em(date=date)
        except _NETWORK_ERRORS as e:
            raise DataFetchError("akshare", "stock_tfp_em", str(e), "network") from e
        except Exception as e:
            raise DataFetchError("akshare", "stock_tfp_em", str(e), "data") from e

        if df is None or df.empty:
            raise DataFetchError("akshare", "stock_tfp_em",
                                 f"无数据: {date}", "data")

        rows = [SuspendInfo(
            symbol=str(r.get("代码", "")),
            name=str(r.get("名称", "")),
            suspend_date=_date(r.get("停牌时间")),
            resume_date=_date(r.get("停牌截止时间")),
            suspend_duration=_str(r.get("停牌期限")),
            suspend_reason=_str(r.get("停牌原因")),
            market=_str(r.get("所属市场")),
            expected_resume_date=_date(r.get("预计复牌时间")),
        ).to_dict() for _, r in df.iterrows()]

        return DataResult(data=rows, source="akshare",
                          meta={"rows": len(rows), "date": date})
