"""接口元数据模型"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class DataFreshness(str, Enum):
    REALTIME = "realtime"           # 盘中实时
    END_OF_DAY = "end_of_day"       # 收盘后
    HISTORICAL = "historical"       # 历史数据
    QUARTERLY = "quarterly"         # 季度披露


class UpdateTiming(str, Enum):
    T_PLUS_0 = "T+0"                          # 盘中实时
    T_PLUS_1_15_30 = "T+1_15:30"             # 收盘后15:30
    T_PLUS_1_16_00 = "T+1_16:00"             # 收盘后16:00
    T_PLUS_1_17_00 = "T+1_17:00"             # 收盘后17:00
    NEXT_TRADE_DAY_9_30 = "next_trade_day_9:30"  # 下一交易日9:30
    QUARTERLY_DISCLOSURE = "quarterly"        # 季度披露


class DataSource(str, Enum):
    AKSHARE = "akshare"
    TUSHARE = "tushare"
    BOTH = "both"


@dataclass
class ToolMeta:
    """
    FinanceData 接口元数据

    Attributes:
        name:           工具名称，如 "tool_get_stock_info"
        description:    一句话功能描述
        domain:         数据领域: stock/index/sector/market/flow/financial/lhb/margin/pool
        entity:         实体类型: stock/index/sector/board/margin/north_capital/lhb/...
        scope:          数据范围: daily/historical/realtime
        data_freshness: 数据新鲜度
        update_timing:  更新时机
        supports_history: 是否支持日期范围查询
        history_start:   历史数据最早日期，如 "20180101"
        cache_ttl:      缓存TTL(分钟)，0=无缓存
        source:         数据源
        source_priority: 优先数据源
        api_name:       实际API名称
        limitations:     已知限制
        return_fields:  主要返回字段
        primary_key:    主键字段
    """
    name: str
    description: str
    domain: str
    entity: str
    scope: str
    data_freshness: DataFreshness
    update_timing: UpdateTiming
    supports_history: bool
    history_start: Optional[str] = None
    cache_ttl: int = 0
    source: DataSource = DataSource.BOTH
    source_priority: str = "akshare"
    api_name: str = ""
    limitations: List[str] = field(default_factory=list)
    return_fields: List[str] = field(default_factory=list)
    primary_key: str = "date"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "entity": self.entity,
            "scope": self.scope,
            "data_freshness": self.data_freshness.value,
            "update_timing": self.update_timing.value,
            "supports_history": self.supports_history,
            "history_start": self.history_start,
            "cache_ttl": self.cache_ttl,
            "source": self.source.value,
            "source_priority": self.source_priority,
            "api_name": self.api_name,
            "limitations": self.limitations,
            "return_fields": self.return_fields,
            "primary_key": self.primary_key,
        }

    @property
    def is_realtime(self) -> bool:
        return self.data_freshness == DataFreshness.REALTIME

    @property
    def is_end_of_day(self) -> bool:
        return self.data_freshness == DataFreshness.END_OF_DAY

    def __str__(self) -> str:
        freshness = self.data_freshness.value
        history = "支持历史" if self.supports_history else "无历史"
        cache = f"缓存{self.cache_ttl}min" if self.cache_ttl > 0 else "无缓存"
        return f"{self.name} [{freshness}] [{history}] [{cache}] - {self.description}"
