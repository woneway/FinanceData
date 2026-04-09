"""涨跌停价格 - 腾讯实时行情 API 实现"""
from finance_data.interface.limit_price.history import LimitPrice
from finance_data.interface.types import DataResult
from finance_data.provider.tencent.client import fetch_quote


class TencentLimitPrice:
    def get_limit_price(self, symbol: str) -> DataResult:
        q = fetch_quote(symbol)
        dt = q.get("datetime", "")
        date_str = dt[:8] if len(dt) >= 8 else ""

        row = LimitPrice(
            symbol=q["code"],
            name=q["name"],
            date=date_str,
            limit_up=q["limit_up"],
            limit_down=q["limit_down"],
            prev_close=q["prev_close"],
            current=q["current"],
        ).to_dict()

        return DataResult(data=[row], source="tencent",
                          meta={"symbol": symbol})
