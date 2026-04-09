"""日频基本面 - 腾讯实时行情 API 实现"""
from finance_data.interface.daily_basic.history import DailyBasic
from finance_data.interface.types import DataResult
from finance_data.provider.tencent.client import fetch_quote


class TencentDailyBasic:
    def get_daily_basic(self, symbol: str) -> DataResult:
        q = fetch_quote(symbol)
        dt = q.get("datetime", "")
        date_str = dt[:8] if len(dt) >= 8 else ""

        row = DailyBasic(
            symbol=q["code"],
            name=q["name"],
            date=date_str,
            pe=q["pe"],
            pb=q["pb"],
            market_cap=q["market_cap"],
            circ_market_cap=q["circ_market_cap"],
            turnover_rate=q["turnover_rate"],
            volume_ratio=q["volume_ratio"],
        ).to_dict()

        return DataResult(data=[row], source="tencent",
                          meta={"symbol": symbol})
