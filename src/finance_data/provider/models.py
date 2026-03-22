from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class StockInfo:
    """
    所有 provider 的个股信息统一输出格式。

    原则：schema 固定，各 provider 尽力填充；无法获取的字段保持默认值（空字符串或 None）。
    """
    # 核心字段（所有 provider 必填）
    symbol: str
    name: str
    industry: str
    list_date: str

    # 基本分类
    area: str = ""
    market: str = ""
    city: str = ""
    exchange: str = ""          # SSE / SZSE
    ts_code: str = ""           # tushare 格式，如 000001.SZ

    # 公司基本信息
    full_name: str = ""
    established_date: str = ""

    # 业务描述
    main_business: str = ""
    introduction: str = ""

    # 管理层
    chairman: str = ""
    legal_representative: str = ""
    general_manager: str = ""
    secretary: str = ""         # 董秘

    # 规模
    reg_capital: Optional[float] = None
    staff_num: Optional[int] = None

    # 联系方式
    website: str = ""
    email: str = ""
    reg_address: str = ""

    # 股权
    actual_controller: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "industry": self.industry,
            "list_date": self.list_date,
            "area": self.area,
            "market": self.market,
            "city": self.city,
            "exchange": self.exchange,
            "ts_code": self.ts_code,
            "full_name": self.full_name,
            "established_date": self.established_date,
            "main_business": self.main_business,
            "introduction": self.introduction,
            "chairman": self.chairman,
            "legal_representative": self.legal_representative,
            "general_manager": self.general_manager,
            "secretary": self.secretary,
            "reg_capital": self.reg_capital,
            "staff_num": self.staff_num,
            "website": self.website,
            "email": self.email,
            "reg_address": self.reg_address,
            "actual_controller": self.actual_controller,
        }
