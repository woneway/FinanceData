# 新增接口完整接入方案

基于 akshare（1118 个函数）、tushare pro（100+ API）、雪球（50+ 端点）三个数据源的全面调研。

> 现有 27 个接口，本方案规划新增约 20 个接口，按优先级分 P0/P1/P2 三期。

---

## 一、现有 vs 缺失能力矩阵

| 能力领域 | 现有工具 | 缺失 | 优先级 |
|---------|---------|------|--------|
| 行情（K线/实时/指数） | 5 个 ✅ | - | - |
| 短线交易（龙虎榜/股池） | 9 个 ✅ | - | - |
| 资金流（个股/板块/北向/融资融券） | 7 个 ✅ | 历史资金流 | P0 |
| 基本面 | 3 个（摘要级） | 三大报表、估值指标 | P0 |
| 股东/持仓 | 0 个 | 十大股东、机构持仓、股东户数 | P0 |
| 大宗交易 | 0 个 | 完整 | P0 |
| 高管增减持 | 0 个 | 完整 | P1 |
| IPO/解禁 | 0 个 | 新股+限售解禁 | P1 |
| 可转债 | 0 个 | 行情+转股价+溢价率 | P1 |
| ETF | 0 个 | 行情+规模 | P1 |
| 港股/AH溢价 | 0 个 | 行情+基本面 | P2 |
| 研报/评级 | 0 个 | 机构评级+目标价 | P2 |
| 公告/新闻 | 0 个 | 公司公告 | P2 |
| 宏观经济 | 0 个 | GDP/CPI/M2/利率 | P2 |

---

## 二、P0 — 高价值接口（8 个新工具）

### 1. `tool_get_valuation_history` — 估值指标

个股历史 PE/PB/PS/股息率/市值，用于估值分析和筛选。

| 字段 | 说明 |
|------|------|
| date | 日期 |
| pe_ttm | 滚动市盈率 |
| pb | 市净率 |
| ps_ttm | 滚动市销率 |
| dv_ratio | 股息率 |
| total_mv | 总市值（亿） |
| circ_mv | 流通市值（亿） |
| turnover_rate | 换手率 |

**数据源方案：**

| Provider | 函数/API | 优缺点 |
|----------|---------|--------|
| **tushare**（主） | `daily_basic(ts_code, start_date, end_date)` | 一次返回多日，含 pe/pe_ttm/pb/ps/dv_ratio/total_mv/circ_mv，需 2000 积分 |
| akshare（备） | `stock_zh_valuation_baidu(symbol, indicator, period)` | 按指标逐个查，需多次调用；period 支持近一年/三年/五年/十年/全部 |
| xueqiu（备） | K线 `indicator=kline,pe,pb,ps,pcf,market_capital` | K线接口附带估值，需登录 cookie |

**推荐：tushare 优先**（字段最全、一次返回），akshare fallback。

---

### 2. `tool_get_income_statement` — 利润表

个股历史利润表（按报告期），核心财务分析基础。

| 字段 | 说明 |
|------|------|
| period | 报告期 (20240331) |
| total_revenue | 营业总收入 |
| revenue | 营业收入 |
| total_cogs | 营业总成本 |
| operate_profit | 营业利润 |
| total_profit | 利润总额 |
| n_income | 净利润 |
| basic_eps | 基本每股收益 |

**数据源方案：**

| Provider | 函数/API | 说明 |
|----------|---------|------|
| **akshare**（主） | `stock_profit_sheet_by_report_em(symbol)` | 东方财富源，无需 token，按报告期/单季/年度 |
| tushare（备） | `income(ts_code, period)` | 需 2000 积分，字段 100+ |
| xueqiu（备） | `/v5/stock/finance/cn/income.json` | 需登录 cookie |

---

### 3. `tool_get_balance_sheet` — 资产负债表

| 字段 | 说明 |
|------|------|
| period | 报告期 |
| total_assets | 总资产 |
| total_liab | 总负债 |
| total_equity | 所有者权益 |
| accounts_receiv | 应收账款 |
| inventories | 存货 |
| money_cap | 货币资金 |
| lt_borr | 长期借款 |

**数据源方案：**

| Provider | 函数/API |
|----------|---------|
| **akshare**（主） | `stock_balance_sheet_by_report_em(symbol)` |
| tushare（备） | `balancesheet(ts_code, period)` |
| xueqiu（备） | `/v5/stock/finance/cn/balance.json` |

---

### 4. `tool_get_cashflow_statement` — 现金流量表

| 字段 | 说明 |
|------|------|
| period | 报告期 |
| n_cashflow_act | 经营活动现金流净额 |
| n_cashflow_inv_act | 投资活动现金流净额 |
| n_cash_flows_fnc_act | 筹资活动现金流净额 |
| free_cashflow | 自由现金流（计算值） |

**数据源方案：**

| Provider | 函数/API |
|----------|---------|
| **akshare**（主） | `stock_cash_flow_sheet_by_report_em(symbol)` |
| tushare（备） | `cashflow(ts_code, period)` |
| xueqiu（备） | `/v5/stock/finance/cn/cash_flow.json` |

---

### 5. `tool_get_top_holders` — 十大股东

个股十大股东（总/流通），追踪机构进出。

| 字段 | 说明 |
|------|------|
| period | 报告期 |
| holder_name | 股东名称 |
| hold_amount | 持股数量（万股） |
| hold_ratio | 持股比例（%） |
| change | 变动（新进/增加/减少/不变） |
| holder_type | 类型（个人/基金/QFII/社保/券商/信托） |

**数据源方案：**

| Provider | 函数/API | 说明 |
|----------|---------|------|
| **akshare**（主） | `stock_gdfx_top_10_em(symbol, date)` / `stock_gdfx_free_top_10_em(symbol, date)` | 东方财富源，含类型分类 |
| tushare（备） | `top10_holders(ts_code)` / `top10_floatholders(ts_code)` | 需 2000 积分 |
| xueqiu（备） | `/v5/stock/f10/cn/top_holders.json?circula=1` | 需登录 cookie |

**参数设计：**
- `symbol`: 股票代码
- `date`: 报告期（可选，默认最新）
- `holder_type`: "total"（十大股东）/ "float"（十大流通股东），默认 "float"

---

### 6. `tool_get_holder_count` — 股东户数

股东人数变化趋势，判断筹码集中度。

| 字段 | 说明 |
|------|------|
| date | 公告日期 |
| holder_num | 股东总户数 |
| holder_num_change | 较上期变动（%） |
| avg_amount | 户均持股数 |
| avg_market_cap | 户均市值 |

**数据源方案：**

| Provider | 函数/API |
|----------|---------|
| **akshare**（主） | `stock_zh_a_gdhs_detail_em(symbol)` |
| tushare（备） | `stk_holdernumber(ts_code)` — 需 600 积分 |

---

### 7. `tool_get_capital_flow_history` — 历史资金流

个股多日历史资金流向（主力/超大/大/中/小单），弥补当前仅有实时的短板。

| 字段 | 说明 |
|------|------|
| date | 日期 |
| main_net_inflow | 主力净流入（万） |
| super_large_net_inflow | 超大单净流入 |
| large_net_inflow | 大单净流入 |
| medium_net_inflow | 中单净流入 |
| small_net_inflow | 小单净流入 |
| main_net_ratio | 主力净占比（%） |

**数据源方案：**

| Provider | 函数/API | 说明 |
|----------|---------|------|
| **akshare**（主） | `stock_individual_fund_flow(stock, market)` | 返回多日历史，含 5 级分类 |
| tushare（备） | `moneyflow(ts_code, start_date, end_date)` | 需 2000 积分，4 档分类 |
| xueqiu（备） | `/v5/stock/capital_flow/history.json?period=5d` | 需登录 cookie |

---

### 8. `tool_get_block_trade` — 大宗交易

大宗交易明细，追踪机构调仓。

| 字段 | 说明 |
|------|------|
| date | 成交日期 |
| symbol | 股票代码 |
| name | 股票名称 |
| price | 成交价 |
| volume | 成交量（万股） |
| amount | 成交额（万元） |
| premium | 溢价率（%） |
| buyer | 买方营业部 |
| seller | 卖方营业部 |

**数据源方案：**

| Provider | 函数/API | 说明 |
|----------|---------|------|
| **akshare**（主） | `stock_dzjy_mrmx(symbol, start_date, end_date)` | 按日查询，含买卖双方 |
| tushare（备） | `block_trade(ts_code, trade_date)` | 需 300 积分 |
| xueqiu（备） | `/v5/stock/trade/blocktrans.json` | 需登录 cookie |

---

## 三、P1 — 中等价值接口（6 个新工具）

### 9. `tool_get_holder_trade` — 高管/股东增减持

| 字段 | date, symbol, name, holder_name, holder_type, change_type(增持/减持), volume, avg_price, change_ratio |
|------|---|

| Provider | 函数/API |
|----------|---------|
| **akshare**（主） | `stock_hold_management_detail_em()` — 全市场；`stock_ggcg_em(symbol)` — 个股 |
| tushare（备） | `stk_holdertrade(ts_code)` — 需 2000 积分 |

---

### 10. `tool_get_restricted_release` — 限售股解禁

| 字段 | date, symbol, name, float_shares, float_ratio, holder_name, share_type |
|------|---|

| Provider | 函数/API |
|----------|---------|
| **akshare**（主） | `stock_restricted_release_summary_em(symbol, start_date, end_date)` + `stock_restricted_release_detail_em(start_date, end_date)` |
| tushare（备） | `share_float(ts_code)` — 需 120 积分 |

**参数：** `start_date`, `end_date`（日期范围），`symbol`（可选，指定个股）

---

### 11. `tool_get_ipo_info` — 新股信息

| 字段 | symbol, name, ipo_date, issue_price, issue_pe, issue_amount, online_amount, listing_date, ballot_rate |
|------|---|

| Provider | 函数/API |
|----------|---------|
| **akshare**（主） | `stock_xgsglb_em(symbol)` — 按板块查；`stock_ipo_declare_em()` — 申报进度 |
| tushare（备） | `new_share()` — 需 120 积分 |

---

### 12. `tool_get_convertible_bond_list` — 可转债列表

| 字段 | bond_code, bond_name, stock_code, stock_name, price, convert_price, premium_rate, remain_size, maturity_date, rating |
|------|---|

| Provider | 函数/API |
|----------|---------|
| **akshare**（主） | `bond_zh_cov()` — 全量可转债 + 溢价率 |
| tushare（备） | `cb_basic()` + `cb_daily()` — 需 2000 积分 |

---

### 13. `tool_get_convertible_bond_history` — 可转债历史行情

| 字段 | date, open, high, low, close, volume, amount |
|------|---|

| Provider | 函数/API |
|----------|---------|
| **akshare**（主） | `bond_zh_hs_cov_daily(symbol)` |
| tushare（备） | `cb_daily(ts_code, start_date, end_date)` |

---

### 14. `tool_get_etf_list` — ETF 列表及实时行情

| 字段 | symbol, name, price, pct_chg, volume, amount, total_nav, discount_rate |
|------|---|

| Provider | 函数/API |
|----------|---------|
| **akshare**（主） | `fund_etf_spot_em()` — 全量 ETF 实时 |
| xueqiu（备） | `/v5/stock/realtime/quotec.json?symbol=SH510300` |

---

## 四、P2 — 扩展接口（6 个新工具）

### 15. `tool_get_stock_pledge` — 股权质押

| Provider | akshare `stock_gpzy_pledge_ratio_em(date)` / tushare `pledge_stat` |

### 16. `tool_get_analyst_rating` — 机构评级

| Provider | akshare `stock_institute_recommend(symbol)` / xueqiu `/v5/stock/f10/cn/report.json` |

### 17. `tool_get_announcement` — 公司公告

| Provider | akshare `stock_notice_report(symbol, date)` |

### 18. `tool_get_hk_stock_history` — 港股历史行情

| Provider | akshare `stock_hk_hist(symbol, period, start_date, end_date, adjust)` |

### 19. `tool_get_ah_premium` — AH 股溢价

| Provider | akshare `stock_zh_ah_spot_em()` |

### 20. `tool_get_macro_indicator` — 宏观经济指标

| Provider | tushare `cn_gdp` / `cn_cpi` / `cn_ppi` / `cn_m` / `shibor` / `shibor_lpr` |

---

## 五、Provider 选型汇总

| 新工具 | 主 Provider | 备 Provider | 原因 |
|--------|-----------|-----------|------|
| 估值指标 | tushare `daily_basic` | akshare baidu | tushare 字段最全、批量查询 |
| 利润表 | akshare `_em` | tushare `income` | akshare 无需 token |
| 资产负债表 | akshare `_em` | tushare `balancesheet` | 同上 |
| 现金流量表 | akshare `_em` | tushare `cashflow` | 同上 |
| 十大股东 | akshare `gdfx_em` | tushare `top10_holders` | akshare 含类型分类 |
| 股东户数 | akshare `gdhs_em` | tushare `holdernumber` | akshare 无需 token |
| 历史资金流 | akshare `fund_flow` | tushare `moneyflow` | akshare 免费 |
| 大宗交易 | akshare `dzjy_em` | tushare `block_trade` | akshare 含买卖方 |
| 高管增减持 | akshare `ggcg_em` | tushare `holdertrade` | akshare 免费 |
| 限售解禁 | akshare `restricted_em` | tushare `share_float` | akshare 免费 |
| 新股 | akshare `xgsglb_em` | tushare `new_share` | akshare 免费 |
| 可转债列表 | akshare `bond_zh_cov` | tushare `cb_basic` | akshare 含溢价率 |
| 可转债行情 | akshare `bond_cov_daily` | tushare `cb_daily` | 同上 |
| ETF 列表 | akshare `etf_spot_em` | xueqiu | akshare 免费 |

---

## 六、实施节奏

### P0（预计 3-5 天）
- 8 个工具，覆盖估值 + 三大报表 + 股东 + 资金流 + 大宗交易
- 实施后接口数：27 → 35

### P1（预计 2-3 天）
- 6 个工具，覆盖增减持 + 解禁 + 新股 + 可转债 + ETF
- 实施后接口数：35 → 41

### P2（按需）
- 6 个工具，覆盖质押 + 评级 + 公告 + 港股 + 宏观
- 实施后接口数：41 → 47

---

## 七、数据源总结

### akshare（主力）
- **1118 个函数**，涵盖 A 股全领域
- 无需 token，数据源为东方财富/同花顺/新浪/百度等公开网页
- 缺点：爬虫模式，部分接口不稳定，IP 可能被限流

### tushare pro（备选）
- **100+ API**，数据质量高，支持批量查询
- 需 token + 积分（2000 分覆盖大部分核心接口）
- 缺点：免费额度有限，高级接口需 5000-8000 积分

### 雪球（补充）
- **50+ 端点**，覆盖 A/H/美股
- K线接口附带 PE/PB/PS/市值等估值数据（独特优势）
- 需登录 cookie（已实现自动提取）
- 缺点：非官方 API，无 SLA 保证，限流策略不透明
