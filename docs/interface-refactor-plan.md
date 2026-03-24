# FinanceData 接口规范化改造计划

## 1. 背景与目标

### 现状问题
1. **命名不一致**：`tool_get_fund_flow` 不清楚是个股还是大盘资金流
2. **元数据缺失**：接口描述缺少实时性、历史查询能力、更新时机等关键维度
3. **校验缺失**：新增接口时无法自动验证是否对齐规范
4. **文档不一致**：CLAUDE.md 与实际接口能力存在偏差

### 目标
1. 建立接口元数据规范（ToolMeta）
2. 统一命名规范
3. 创建 API 文档对齐校验机制
4. 定义新增接口的 Skill（技能卡片）

---

## 2. 接口元数据规范

### 2.1 ToolMeta 数据结构

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ToolMeta:
    # === 核心标识 ===
    name: str                          # 工具名称: "tool_get_xxx"
    description: str                   # 一句话功能描述

    # === 数据特征 ===
    domain: str                       # 领域: stock/index/sector/market/flow/financial/lhb
    entity: str                       # 实体: stock/index/sector/board/margin/north_flow
    scope: str                         # 范围: daily/historical/realtime

    # === 时效性 ===
    data_freshness: str               # realtime | end_of_day | historical | quarterly
    update_timing: str                # 更新时机:
                                       #   T+0 (盘中实时)
                                       #   T+1_15:30 (收盘后15:30)
                                       #   T+1_17:00 (收盘后17:00)
                                       #   next_trade_day_9:30 (下一交易日9:30)
                                       #   quarterly (季度披露)

    # === 查询能力 ===
    supports_history: bool            # 是否支持日期范围查询
    history_start: Optional[str]      # 历史数据最早日期，如 "20180101"

    # === 缓存 ===
    cache_ttl: int = 0               # 缓存TTL(分钟)，0=无缓存

    # === 数据源 ===
    source: str                       # akshare | tushare | both
    source_priority: str = "akshare" # 优先数据源
    api_name: str = ""                # 实际API名称，如 "stock_margin_sse"
    limitations: List[str] = field(default_factory=list)  # 已知限制

    # === 返回值 ===
    return_fields: List[str] = field(default_factory=list)  # 主要返回字段
    primary_key: str = "date"        # 主键字段
```

### 2.2 命名规范

**格式：** `get_{entity}_{scope}_{attribute}`

| 实体 | 英文 | 说明 |
|------|------|------|
| 股票/个股 | stock | |
| 大盘/指数 | market / index | market=全市场, index=指数 |
| 板块 | sector / board | sector=行业, board=概念 |
| 资金流 | capital_flow | 资金流向 |
| 北向资金 | north_capital | 陆股通北向 |
| 融资融券 | margin | |
| 龙虎榜 | lhb | |
| 筹码 | chip | |

**示例：**

| 当前名称 | 规范名称 | 说明 |
|---------|---------|------|
| `tool_get_fund_flow` | `tool_get_stock_capital_flow` | 个股资金流向 |
| `tool_get_north_flow` | `tool_get_market_north_capital` | 北向资金流 |
| `tool_get_sector_fund_flow` | `tool_get_sector_capital_flow` | 板块资金流 |
| `tool_get_market_stats` | `tool_get_market_stats_daily` | 市场每日统计 |

**兼容性策略：** 新增规范名称，保留旧名称作为别名（deprecated）

---

## 3. API 文档对齐校验

### 3.1 校验规则

```python
# src/finance_data/provider/metadata/validator.py

RULES = {
    # 必须有 docstring
    "has_docstring": True,

    # docstring 必须包含以下章节
    "docstring_sections": [
        "数据源",
        "实时性",
        "历史查询",
        "参数说明",
        "返回值",
    ],

    # 参数命名规范
    "param_naming": {
        "单日查询": "trade_date",
        "日期范围": "start_date / end_date",
        "股票代码": "symbol",
        "K线周期": "period",
    },

    # 返回值必须包含 date 字段
    "required_return_fields": ["date"],
}
```

### 3.2 校验脚本

```bash
# 校验所有接口描述是否对齐
python -m finance_data.provider.metadata.validate

# 输出示例:
# [PASS] tool_get_stock_info - docstring 完整
# [PASS] tool_get_kline - 参数命名正确
# [FAIL] tool_get_market_stats - 缺少"实时性"描述
# [FAIL] tool_get_north_flow - 缺少"历史查询"说明
```

### 3.3 CLAUDE.md 同步校验

每次新增接口后，自动校验：
1. CLAUDE.md 中的接口数量与实际一致
2. 接口描述与 ToolMeta 一致
3. 数据源优先级与实现一致

---

## 4. 新增接口 Skill

### 4.1 Skill 文件位置

```
FinanceData/.claude/skills/
└── add-new-interface.md
```

### 4.2 Skill 内容

详见: `.claude/skills/add-new-interface.md`

---

## 5. 实施步骤

### Phase 1: 基础设施（1天）
- [ ] 创建 `src/finance_data/provider/metadata/` 目录
- [ ] 定义 `ToolMeta` 数据类
- [ ] 创建 `TOOL_REGISTRY` 配置字典
- [ ] 实现 `validator.py` 校验脚本

### Phase 2: 存量接口规范化（2天）
- [ ] 为 27 个现有接口生成 ToolMeta
- [ ] 更新所有 docstring 对齐规范
- [ ] 运行校验，修复不符合项
- [ ] 更新 CLAUDE.md 同步

### Phase 3: 命名优化（可选，1天）
- [ ] 确定需要重命名的接口列表
- [ ] 创建别名兼容机制
- [ ] 逐步切换到规范名称

### Phase 4: Skill 落地（0.5天）
- [ ] 创建 `.claude/skills/add-new-interface.md`
- [ ] 更新 CLAUDE.md 中的"新增接口流程"

### Phase 5: 自动化（持续）
- [ ] 在 CI 中集成校验
- [ ] 新增接口时自动检查 ToolMeta

---

## 6. 附录

### 6.1 数据源实时性速查

| 数据源 | 实时性 | 说明 |
|--------|--------|------|
| akshare 实时行情 | T+0 | 盘中实时更新 |
| tushare 日线 | T+1_16:00 | 次日16:00 |
| akshare 融资融券 | T+1_17:00 | 次日17:00 |
| tushare 财报 | quarterly | 季度披露 |
| 北向资金 | T+1_15:30 | 收盘后30分钟 |

### 6.2 接口分类速查

| 类别 | 接口 |
|------|------|
| **实时(T+0)** | get_realtime_quote, get_index_quote, get_sector_rank, get_fund_flow, get_chip |
| **收盘后** | get_kline, get_index_history, get_market_stats, get_zt_pool, get_lhb_* |
| **历史查询** | get_kline, get_index_history, get_margin, get_lhb_detail, get_trade_calendar |
| **Tushare专有** | get_trade_calendar, get_margin, get_margin_detail |
| **Akshare专有** | get_market_stats, get_north_flow, get_sector_fund_flow, get_zt_pool |
