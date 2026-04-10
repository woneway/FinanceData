# 上游对齐记录

## 日线 (daily)

| 维度 | tushare (doc_id=27) | akshare (腾讯源 stock_zh_a_hist_tx) |
|------|---------------------|-------------------------------------|
| 调用方式 | `pro.daily(ts_code, start_date, end_date)` | `ak.stock_zh_a_hist_tx(symbol, start_date, end_date, adjust)` |
| 字段 | trade_date, open, high, low, close, vol, amount, pct_chg | date, open, high, low, close, amount |
| vol 单位 | 手（×100→股） | amount 列实为成交量手（×100→股） |
| amount 单位 | 千元（×1000→元） | 无真实成交额，需从均价估算 |
| pct_chg | 有，百分比 | 无，需从前收盘价计算 |
| 复权 | 通过 adj 参数 | 通过 adjust 参数 (qfq/hfq/"") |
| 历史范围 | 1990 年至今 | 取决于腾讯数据覆盖 |
| 更新时间 | T+1 约 16:00 | 收盘后 |
| 状态 | ✅ 稳定可用 | ✅ 稳定可用 |

## 周线 (weekly)

| 维度 | tushare (doc_id=336 每日更新) | akshare (stock_zh_a_hist period=weekly) |
|------|-------------------------------|----------------------------------------|
| 调用方式 | `pro.weekly(ts_code, start_date, end_date)` | `ak.stock_zh_a_hist(symbol, period="weekly", start_date, end_date, adjust)` |
| 语义 | 每日更新的周线，含当前未完成周 | 东财源周线 |
| 字段 | trade_date, open, high, low, close, vol, amount, pct_chg | 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率 |
| vol 单位 | 手（×100→股） | 股 |
| amount 单位 | 千元（×1000→元） | 元 |
| 复权 | 通过 adj 参数 | 通过 adjust 参数 |
| 状态 | ✅ 稳定可用 | ⚠️ 需验证东财源是否需代理绕过 |
| 未完成周 | 包含 | 待验证 |

## 月线 (monthly)

| 维度 | tushare (doc_id=336 每日更新) | akshare (stock_zh_a_hist period=monthly) |
|------|-------------------------------|----------------------------------------|
| 调用方式 | `pro.monthly(ts_code, start_date, end_date)` | `ak.stock_zh_a_hist(symbol, period="monthly", start_date, end_date, adjust)` |
| 语义 | 每日更新的月线，含当前未完成月 | 东财源月线 |
| 字段 | 同周线 | 同周线 |
| vol 单位 | 手（×100→股） | 股 |
| amount 单位 | 千元（×1000→元） | 元 |
| 状态 | ✅ 稳定可用 | ⚠️ 需验证东财源是否需代理绕过 |
| 未完成月 | 包含 | 待验证 |

## 结论

1. **日线**: tushare 主源 + akshare(腾讯) fallback，两源均稳定
2. **周线/月线**: tushare 主源稳定；akshare fallback 需使用 `ak.stock_zh_a_hist()` (东财源) + `ensure_eastmoney_no_proxy()` 代理绕过
3. **分钟级**: 本次不再提供，下线
4. **单位统一**: tushare 需 vol×100、amount×1000；akshare 东财源 volume/amount 已是股/元
