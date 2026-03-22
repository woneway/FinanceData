from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class StockInfo:
    """所有 provider 的个股信息统一输出格式"""
    # 核心字段（所有 provider 必填）
    symbol: str
    name: str
    industry: str
    list_date: str

    # 基本信息
    area: str = ""
    market: str = ""
    full_name: str = ""
    established_date: str = ""
    ts_code: str = ""

    # 业务描述
    main_business: str = ""
    introduction: str = ""

    # 管理层
    chairman: str = ""
    legal_representative: str = ""

    # 规模
    reg_capital: Optional[float] = None
    staff_num: Optional[int] = None

    # 联系方式
    website: str = ""
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
            "full_name": self.full_name,
            "established_date": self.established_date,
            "ts_code": self.ts_code,
            "main_business": self.main_business,
            "introduction": self.introduction,
            "chairman": self.chairman,
            "legal_representative": self.legal_representative,
            "reg_capital": self.reg_capital,
            "staff_num": self.staff_num,
            "website": self.website,
            "reg_address": self.reg_address,
            "actual_controller": self.actual_controller,
        }
