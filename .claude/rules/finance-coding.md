# FinanceData 编码规范

## 命名规则

| 层 | 类名模式 | 示例 |
|----|---------|------|
| Provider | `{Source}{Domain}{Type}` | `TushareKlineHistory`, `AkshareSectorRank` |
| Service | `_{DomainType}Dispatcher`（私有） | `_KlineHistoryDispatcher` |
| Service 实例 | `snake_case`（模块级） | `kline_history = _build_kline_history()` |
| Interface Protocol | `{Entity}{Type}Protocol` | `KlineHistoryProtocol`, `RealtimeQuoteProtocol` |
| Interface Model | `{Entity}{Type}` (dataclass) | `KlineBar`, `RealtimeQuote`, `IndexBar` |
| MCP Tool | `tool_{action}_{entity}_{scope}` | `tool_get_kline_daily_history`, `tool_get_stock_quote_realtime` |
| Client 方法 | `{entity}_{sub}`（简洁） | `fd.kline_daily()`, `fd.quote()`, `fd.board_member()` |
| 文件名 | `provider/{source}/{domain}/{type}.py` | `provider/tushare/kline/history.py` |
| 测试文件 | `test_{source}.py` 或 `test_{source}_{specific}.py` | `test_akshare.py`, `test_akshare_lhb_sina.py` |

## Scope 分类（4 种）

| scope | 含义 | 参数特征 | 示例 |
|-------|------|---------|------|
| `history` | 支持日期范围查询 | start_date/end_date | kline_daily, lhb_detail, margin |
| `realtime` | 盘中实时 T+0 | 无日期参数 | quote, market_stats, hot_rank |
| `daily` | 日频快照，仅单日 | date/trade_date | zt_pool, suspend, ths_hot |
| `snapshot` | 按 symbol 查全量 | 仅 symbol | stock_info, north_capital |

## Domain 分类（12 个）

stock, kline, quote, index, board, fundamental, lhb, pool, north_flow, margin, market, cashflow

## 数据单位（统一标准）

| 字段 | 单位 | 说明 |
|------|------|------|
| `volume` | 股 | tushare 返回手（×100），akshare 视上游而定 |
| `amount` | 元 | tushare 返回千元（×1000） |
| `price`/`open`/`high`/`low`/`close` | 元 | |
| `pct_chg` | % | 百分比 |
| `market_cap` | 元 | |
| 日期 | YYYYMMDD | 8位数字字符串，无分隔符 |
| 时间戳 | ISO 8601 | 如 `2026-03-27T15:00:00+08:00` |

## 错误处理

所有 provider 使用 `DataFetchError(source, func, reason, kind)` 统一抛出：

```python
_NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)

try:
    df = ak.some_function(...)
    if df is None or df.empty:
        raise DataFetchError("akshare", "some_function", "无数据", "data")
    # ... 转换
    return DataResult(data=rows, source="akshare", meta={...})
except DataFetchError:
    raise
except _NETWORK_ERRORS as e:
    raise DataFetchError("akshare", "some_function", str(e), "network") from e
except Exception as e:
    raise DataFetchError("akshare", "some_function", str(e), "data") from e
```

**kind 类型（4 种）**：`network`（网络错误）、`data`（空数据/格式错误）、`auth`（token/权限）、`quota`（限流）

## MCP Tool Docstring 规范

每个 `@mcp.tool()` 函数的 docstring 必须包含以下章节（由 validator 自动检查）：

```python
@mcp.tool()
async def tool_get_xxx(...) -> str:
    """
    一句话功能描述。

    数据源: akshare(新浪) 优先，tushare fallback
    实时性: 收盘后更新（T+1_17:00）
    历史查询: 支持（2020年至今）

    Args:
        symbol: 股票代码，如 "000001"
        start: 开始日期 YYYYMMDD

    Returns:
        JSON 列表，每条记录包含：symbol(代码)、name(名称)、
        close(收盘价元)、volume(成交量股)、amount(成交额元)

    Note:
        akshare 支持完整日期范围；tushare fallback 仅支持单日查询。
    """
```

## ToolMeta 注册

每个 MCP tool 必须在 `provider/metadata/registry.py` 注册 `ToolMeta`：

```python
"tool_get_xxx": ToolMeta(
    name="tool_get_xxx",
    description="一句话描述",
    domain="kline",                           # 领域
    entity="stock",                           # 实体类型
    scope="daily",                            # daily/historical/realtime/quarterly
    data_freshness=DataFreshness.END_OF_DAY,  # REALTIME/END_OF_DAY/HISTORICAL/QUARTERLY
    update_timing=UpdateTiming.T_PLUS_1_16_00,
    supports_history=True,
    history_start="20200101",                 # 可选
    source=DataSource.BOTH,                   # AKSHARE/TUSHARE/TENCENT/BOTH/MULTI
    source_priority="akshare",
    api_name="stock_xxx_sina",                # 上游 API 函数名
    primary_key="date",
    return_fields=["date", "symbol", "close", "volume"],
),
```

## 测试规范

- mock 数据注入 provider 层（patch akshare/tushare 函数）
- 每个 provider 类至少覆盖：正常返回 / 空数据抛错 / 网络错误抛错
- 跨 provider 单位一致性测试在 `tests/provider/test_unit_consistency.py`

```python
def test_returns_data_result(mock_df):
    with patch("...ak.some_function", return_value=mock_df):
        result = SomeProvider().get_xxx(...)
    assert isinstance(result, DataResult)
    assert result.source == "akshare"
    row = result.data[0]
    assert row["volume"] == expected_volume  # 验证单位转换

def test_empty_raises():
    with patch("...ak.some_function", return_value=pd.DataFrame()):
        with pytest.raises(DataFetchError) as exc:
            SomeProvider().get_xxx(...)
    assert exc.value.kind == "data"
```
