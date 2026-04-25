<!-- 用 openspec/templates/upstream-alignment.template.md 落地。 -->

# 上游对齐记录（retroactive，基于 ab32a22 + c010fe9 实际接入反推）

## 分钟 K 线（5/15/30/60min）

| 维度 | baostock | tushare（未启用，仅参考） |
|------|----------|---------------------------|
| 调用方式 | `bs.query_history_k_data_plus(code, fields, start_date, end_date, frequency, adjustflag)`，code 形如 `sh.600000` / `sz.000001`，frequency ∈ {`5`, `15`, `30`, `60`} | `pro.stk_mins(ts_code, freq, start_date, end_date)`，需用户分钟权限 |
| 字段 | `date,time,code,open,high,low,close,volume,amount`（time 格式 `YYYYMMDDHHmmssmmm`，截取 8:14 得 `HHmmss`） | trade_time, open, high, low, close, vol, amount |
| volume 单位 | 股（无需换算） | 手（×100→股） |
| amount 单位 | 元（无需换算） | 千元（×1000→元） |
| 复权 | `adjustflag` 参数：`2`=qfq，`1`=hfq，`3`=none；项目映射 `_ADJ_MAP` | `adj` 参数：`qfq` / `hfq` / `None` |
| 历史范围 | 自 2020 年起 | 取决于用户权限层级 |
| 更新时间 | 收盘后约 T 当日 17:00 | T 当日盘后 |
| 状态 | ✅ 稳定（需 baostock>=0.9.1） | 🟡 受 tushare 分钟权限限制，未启用 |

**结论**：分钟 K 线主源 baostock，无 fallback。tushare 分钟接口因权限受限，且单位需要换算，未启用。

### 权限敏感性说明
- baostock 是免费数据源，但其上游服务策略可能变化（c010fe9 揭露：2026-04-14 服务地址迁移导致旧版本不可用）。
- 用户安装时 MUST 拿到 `baostock >= 0.9.1`，否则登录卡死、分钟接口不可用。
- service 层不做静默 fallback：上游不可用时直接抛 `DataFetchError`，让维护方主动处理（避免数据静默缺失）。

### 字段映射（baostock 原始 → 项目 MinuteKlineBar）

| baostock 原始 | MinuteKlineBar 字段 | 转换 |
|---------------|---------------------|------|
| `date`（YYYY-MM-DD） | `date` | `_parse_date()` 去掉 `-` |
| `time`（YYYYMMDDHHmmssmmm） | `time` | `raw_time[8:14]` 截取 `HHmmss` |
| `code`（sh.000001） | `symbol` | 调用方传入的 symbol，去掉前缀（`code_clean = symbol.split(".")[0].lstrip("shsz.")`） |
| `open/high/low/close` | 同名 | `_safe_float()`，无单位换算 |
| `volume` | `volume` | `_safe_float()`，单位即「股」 |
| `amount` | `amount` | `_safe_float()`，单位即「元」 |
| 调用方参数 `adj` | `adj` | 直接保留（qfq/hfq/none） |
| 调用方参数 `period` | `period` | 直接保留（5min/15min/30min/60min） |

## 结论

1. **分钟 K 线**: baostock 主源，无 fallback；与日线 / 周线 / 月线的「主源 + fallback」格局不同，受免费数据源生态限制。
2. **单位统一**: baostock 已与项目对齐（volume 股、amount 元），无需 provider 层换算。这是选择 baostock 而非 tushare 的关键理由之一（tushare 需 vol×100 + amount×1000）。
3. **代理绕过**: 不需要。baostock 不走东财，与 `ensure_eastmoney_no_proxy()` 无关。
4. **依赖锁定**: 必须 `baostock>=0.9.1`（已在 `pyproject.toml` 声明）。
5. **不覆盖范围**:
   - tushare 分钟接口（`stk_mins`）：因用户权限受限且单位需换算，本 change 不接入；未来若 tushare 权限放开可作为 fallback。
   - 日线分钟（1min）：baostock 不支持，不涉及。
   - 历史数据 < 2020 年：baostock 上游限制。
