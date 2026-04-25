<!-- 用 openspec/templates/upstream-alignment.template.md 落地。基于 1e65aba commit 的 provider 代码事实反推。 -->

# 上游对齐记录（retroactive）

## 技术因子（tushare stk_factor_pro）

| 维度 | tushare `stk_factor_pro` |
|------|--------------------------|
| 调用方式 | `pro.stk_factor_pro(ts_code, trade_date, start_date, end_date)`，参数全为可选；典型组合：单股票多日（ts_code + start/end）或全市场单日（trade_date） |
| 字段（节选） | `trade_date, ts_code, close, open, high, low, pre_close, change, pct_chg, vol, amount, turnover_rate, turnover_rate_f, volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, total_share, float_share, free_share, total_mv, circ_mv, dv_ratio, dv_ttm, free_mv, ma_bfq_5/10/20/30/60/90/250, macd_dif_bfq, macd_dea_bfq, macd_bfq, kdj_k_bfq, kdj_d_bfq, kdj_bfq, rsi_bfq_6/12/24, boll_upper_bfq, boll_mid_bfq, boll_lower_bfq, cci_bfq` |
| 单位 | `vol` 单位是手（×100→股）；`amount` 千元（×1000→元）；`total_share/float_share/free_share/total_mv/circ_mv/free_mv` 万股 / 万元（×10000→股 / 元）；`pct_chg/turnover_rate/dv_ratio` 百分比；技术指标无单位 |
| 复权 | tushare 在字段名中后缀显式：`bfq` = 不复权（项目使用），`qfq` / `hfq` 后缀字段未消费 |
| 历史范围 | 2005-01-01 至今 |
| 更新时间 | T+1 约 16:00（与日线一致） |
| 状态 | ✅ 稳定（需 5000 积分权限，单次最多 10000 条） |

**结论**：单源 tushare，无 fallback。akshare 没有等价的「技术因子专业版」聚合接口；自行计算需补 250 日窗口数据，不在本范围。

### 字段映射（tushare 原始 → 项目 StockFactor）

| tushare 字段 | StockFactor 字段 | 转换 |
|---|---|---|
| `vol` | `volume` | × 100 → 股 |
| `amount` | `amount` | × 1000 → 元 |
| `total_share/float_share/free_share` | 同名 | × 10000 → 股 |
| `total_mv/circ_mv/free_mv` | 同名 | × 10000 → 元 |
| `ma_bfq_5/10/20/30/60/90/250` | `ma5/10/20/30/60/90/250` | 去前缀「ma_bfq_」 |
| `macd_dif_bfq/macd_dea_bfq/macd_bfq` | `macd_dif/macd_dea/macd` | 去后缀「_bfq」 |
| `kdj_k_bfq/kdj_d_bfq/kdj_bfq` | `kdj_k/kdj_d/kdj_j` | 去后缀 + j 字段名特殊（kdj_bfq → kdj_j） |
| `rsi_bfq_6/12/24` | `rsi_6/12/24` | 去前缀「rsi_bfq_」 |
| `boll_upper_bfq/boll_mid_bfq/boll_lower_bfq` | `boll_upper/boll_mid/boll_lower` | 去后缀「_bfq」 |
| `cci_bfq` | `cci` | 去后缀 |
| `turnover_rate / turnover_rate_f / pe / pe_ttm / pb / ps / ps_ttm / dv_ratio / dv_ttm` | 同名 | 直接保留（百分比 / 倍数） |

## 板块资金流（tushare moneyflow_ind_dc）

| 维度 | tushare `moneyflow_ind_dc` |
|------|----------------------------|
| 调用方式 | `pro.moneyflow_ind_dc(trade_date, start_date, end_date, ts_code, content_type)`，参数全为可选 |
| 字段 | `trade_date, ts_code, name, content_type, pct_chg, close, net_amount, net_amount_rate, buy_elg_amount, buy_lg_amount, buy_md_amount, buy_sm_amount, buy_sm_amount_stock, rank` |
| 单位 | `pct_chg/net_amount_rate` 百分比；`net_amount/buy_*_amount` 万元（× 10000 → 元，需 provider 适配，待核实当前实现） |
| `content_type` | `概念` / `行业` / `地域` 三选一 |
| 历史范围 | 2020-01-01 至今 |
| 更新时间 | T+1 约 17:00 |
| 状态 | ✅ 稳定 |

**结论**：单源 tushare，无 fallback。akshare 有同源东财数据但字段格式不一致，未接入。

## 大盘资金流（tushare moneyflow_mkt_dc）

| 维度 | tushare `moneyflow_mkt_dc` |
|------|----------------------------|
| 调用方式 | `pro.moneyflow_mkt_dc(trade_date, start_date, end_date)` |
| 字段 | `trade_date, close_sh, pct_change_sh, close_sz, pct_change_sz, net_amount, net_amount_rate, buy_lg_amount, buy_elg_amount` |
| 单位 | 同板块资金流 |
| 历史范围 | 2020-01-01 至今 |
| 更新时间 | T+1 约 17:00 |
| 状态 | ✅ 稳定 |

**结论**：单源 tushare，无 fallback。

## 结论

1. **技术因子**: tushare `stk_factor_pro` 单源，无 fallback；需 5000 积分；单次最多 10000 条限制需要在 service 层做窗口拆分（当前实现未拆分，是潜在 spec drift，详见 acceptance.md）。
2. **板块资金流 / 大盘资金流**: tushare `moneyflow_ind_dc / moneyflow_mkt_dc` 单源，T+1 17:00 更新；与 akshare 东财源未对齐。
3. **单位统一**: 三个接口均涉及 tushare 标准换算（vol×100 / amount×1000 / 万元 × 10000）；技术因子的「字段名前/后缀去除」是项目统一约定，需在 spec 中显式说明。
4. **代理绕过**: 不需要。tushare 走官方 API，不是东财直连。
5. **不覆盖范围**:
   - akshare 等价资金流接口：未接入。
   - tushare `stk_factor`（非 pro）：未接入，因 pro 字段更全。
   - 实时资金流（盘中）：tushare 暂无对等接口，本 change 不涉及。
