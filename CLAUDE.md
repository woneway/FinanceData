# FinanceData

金融数据服务，支持 MCP（AI Agent）和 Python library 两种接入方式。

## 环境变量

- `TUSHARE_TOKEN`：tushare API token（tushare 接口必须）
- `TUSHARE_API_URL`：tushare API 地址（可选，默认官方地址；使用第三方代理时设置）
- `XUEQIU_COOKIE`：雪球登录 cookie 字符串（可选，手动指定时优先级最高）

### 雪球 Cookie 自动获取

cookie 通过 4 层 fallback 自动获取，通常无需手动配置：

1. **环境变量** `XUEQIU_COOKIE`（手动设置时最优先）
2. **浏览器自动提取**：从 Chrome 所有 Profile / Safari 读取（需 `browser-cookie3`）
3. **文件缓存** `~/.finance_data/xueqiu_cookie.json`（24h TTL）
4. **访客 cookie**（访问雪球首页获取，仅支持实时行情，不支持 K 线）

检测逻辑：`finance_data.provider.xueqiu.client.has_login_cookie()`

## 开发

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pip install -e ".[browser]"  # 可选：启用浏览器 cookie 自动提取
.venv/bin/pytest tests/ -v
```

## 架构

### 四层分离（Domain-first）

```
mcp/server.py → service/<domain>.py → provider/<source>/<domain>/ → interface/<domain>/
   (薄封装)        (Dispatcher)          (数据源实现)                (Protocol + Model)
```

```
src/finance_data/
├── interface/          # 协议层：Protocol + dataclass models
│   └── <domain>/       #   每个领域一个目录
│       └── history.py  #   Protocol 定义 + dataclass（含 to_dict()）
├── provider/           # 数据源实现（akshare/tushare/xueqiu）
│   ├── akshare/        #   无需 token，上游源：新浪/腾讯/同花顺/乐估/交易所
│   ├── tushare/        #   需 TUSHARE_TOKEN
│   ├── xueqiu/         #   海外可达，实时行情无需认证，K线需 cookie
│   ├── metadata/       #   registry.py（ToolMeta）+ validator.py + models.py
│   └── symbol.py       #   跨 provider 股票代码转换
├── service/            # 业务编排层：Dispatcher 管理多 provider fallback 链
│   └── <domain>.py     #   每个领域一个 service
├── dashboard/          # 健康监控看板（FastAPI + React）
│   ├── app.py          #   FastAPI 路由
│   ├── health.py       #   逐 tool×provider 探测
│   ├── consistency.py  #   跨 provider 数据一致性比较
│   ├── metrics.py      #   调用次数/耗时/成功率
│   └── static/         #   Vite 构建产物
└── mcp/
    └── server.py       #   MCP tool 定义，调用 service 层

tests/
├── provider/<domain>/  # 按领域组织，test_akshare.py / test_tushare.py 等
├── mcp/                # MCP 层测试
└── integration_test.py # 集成测试脚本

frontend/               # Dashboard 前端源码（React + shadcn/ui + Tailwind）
```

### Provider 优先级

`akshare`（无需 token）→ `tushare`（需 `TUSHARE_TOKEN`）→ `xueqiu`（海外可达）

Service 层在模块加载时根据 token/cookie 可用性动态构建 provider 链：

```python
def _build_kline_history():
    providers = [AkshareKlineHistory()]          # 总是可用
    if os.getenv("TUSHARE_TOKEN"):
        providers.append(TushareKlineHistory())  # 有 token 才加入
    if has_login_cookie():
        providers.append(XueqiuKlineHistory())   # 有 cookie 才加入
    return _KlineHistoryDispatcher(providers=providers)
```

### 东财接口与代理绕过

部分东财源（`_em` 后缀函数）可用，但**必须绕过本地代理**直连。

**问题根因**：本地 Clash/V2Ray 代理（`127.0.0.1:7890`）对东财 HTTPS 连接处理异常，导致 `ConnectionResetError` / SSL 错误。akshare 内部使用 `requests`，会自动拾取 `http_proxy`/`https_proxy` 环境变量，流量被路由到代理后失败。直连则正常（`curl --noproxy '*' https://push2ex.eastmoney.com/...` 返回 200）。

**解决方案**：`provider/akshare/_proxy.py` 提供 `ensure_eastmoney_no_proxy()`，将 `eastmoney.com` 加入 `no_proxy` 环境变量，使 `requests` 对东财域名走直连。

**使用规则**：
- 新增使用东财源（`_em` 后缀）的 provider，必须在模块顶部调用：
  ```python
  from finance_data.provider.akshare._proxy import ensure_eastmoney_no_proxy
  ensure_eastmoney_no_proxy()
  ```
- **已恢复**：`push2ex.eastmoney.com` 端点（涨停池 4 个 + 北向资金 1 个）
- **仍不可达**：`push2.eastmoney.com` 端点（板块资金流 `stock_sector_fund_flow_rank`，该域名直连也不通）

**排查新的东财接口不可用时**：先用 `curl --noproxy '*'` 测试直连，再用 `curl -x http://127.0.0.1:7890` 测试代理，区分是域名封禁还是代理问题。

## 编码规范

### 命名规则

| 层 | 类名模式 | 示例 |
|----|---------|------|
| Provider | `{Source}{Domain}{Type}` | `TushareKlineHistory`, `AkshareSectorRank` |
| Service | `_{DomainType}Dispatcher`（私有） | `_KlineHistoryDispatcher` |
| Service 实例 | `snake_case`（模块级） | `kline_history = _build_kline_history()` |
| Interface Protocol | `{Entity}{Type}Protocol` | `KlineHistoryProtocol`, `RealtimeQuoteProtocol` |
| Interface Model | `{Entity}{Type}` (dataclass) | `KlineBar`, `RealtimeQuote`, `IndexBar` |
| MCP Tool | `tool_{action}_{entity}_{scope}` | `tool_get_kline_history`, `tool_get_realtime_quote` |
| 文件名 | `provider/{source}/{domain}/{type}.py` | `provider/tushare/kline/history.py` |
| 测试文件 | `test_{source}.py` 或 `test_{source}_{specific}.py` | `test_akshare.py`, `test_akshare_lhb_sina.py` |

### 数据单位（统一标准）

| 字段 | 单位 | 说明 |
|------|------|------|
| `volume` | 股 | tushare 返回手（×100），akshare 视上游而定 |
| `amount` | 元 | tushare 返回千元（×1000） |
| `price`/`open`/`high`/`low`/`close` | 元 | |
| `pct_chg` | % | 百分比 |
| `market_cap` | 元 | |
| 日期 | YYYYMMDD | 8位数字字符串，无分隔符 |
| 时间戳 | ISO 8601 | 如 `2026-03-27T15:00:00+08:00` |

### 错误处理

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

### MCP Tool Docstring 规范

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

### ToolMeta 注册

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
    source=DataSource.BOTH,                   # AKSHARE/TUSHARE/BOTH
    source_priority="akshare",
    api_name="stock_xxx_sina",                # 上游 API 函数名
    primary_key="date",
    return_fields=["date", "symbol", "close", "volume"],
),
```

### 测试规范

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

## 新增接口流程

> 使用 `.claude/skills/add-new-interface.md` Skill 获得完整步骤指导。

1. **interface 层**：在 `interface/<domain>/` 定义 Protocol + dataclass model（含 `to_dict()`）
2. **provider 层**：在 `provider/<source>/<domain>/` 实现 provider 类
3. **service 层**：在 `service/<domain>.py` 创建 Dispatcher + `_build_*()` + 模块级实例
4. **mcp 层**：在 `mcp/server.py` 添加 `@mcp.tool()` 函数（含规范 docstring）
5. **metadata**：在 `provider/metadata/registry.py` 注册 ToolMeta
6. **health**：在 `dashboard/health.py` 的 `_TOOL_PROVIDERS` 和 `_get_test_params()` 添加条目
7. **测试**：在 `tests/provider/<domain>/` 添加 mock 测试
8. **校验**：`python -c "from finance_data.provider.metadata.validator import run_validation_report; print(run_validation_report())"`
9. **更新本文件**：更新下方接口列表

## 当前接口（25 个）

| Tool | 领域 | 说明 |
|------|------|------|
| `tool_get_stock_info_history` | stock | 个股基本信息，tushare+xueqiu |
| `tool_get_kline_history` | kline | K线历史数据（daily/weekly/monthly/分钟级），akshare(腾讯+新浪)+tushare+xueqiu |
| `tool_get_realtime_quote` | realtime | 实时行情（含 20 分钟缓存），tushare+xueqiu |
| `tool_get_index_quote_realtime` | index | 大盘指数实时行情，akshare(新浪)+tushare+xueqiu |
| `tool_get_index_history` | index | 大盘指数历史 K线，akshare(新浪)+tushare+xueqiu |
| `tool_get_sector_rank_realtime` | sector | 行业板块涨跌排名，akshare(同花顺) |
| `tool_get_chip_distribution_history` | chip | 个股筹码分布（获利比例、成本、集中度），仅 tushare |
| `tool_get_financial_summary_history` | fundamental | 财务摘要（营收、净利润、ROE、毛利率），akshare(新浪)+tushare+xueqiu |
| `tool_get_dividend_history` | fundamental | 历史分红记录，akshare(同花顺)+tushare+xueqiu |
| `tool_get_stock_capital_flow_realtime` | cashflow | 个股资金流向（主力净流入），xueqiu |
| `tool_get_trade_calendar_history` | calendar | 交易日历（is_open 标记），tushare+akshare(新浪) |
| `tool_get_market_stats_realtime` | market | 市场涨跌统计（盘中实时，涨/跌/平家数），akshare(乐估) |
| `tool_get_lhb_detail` | lhb | 龙虎榜每日上榜详情（按日期范围），仅 tushare |
| `tool_get_lhb_stock_stat` | lhb | 个股上榜统计（近5日），akshare(新浪) |
| `tool_get_lhb_active_traders` | lhb | 活跃游资营业部统计，akshare(新浪) |
| `tool_get_lhb_trader_stat` | lhb | 营业部龙虎榜战绩排行，akshare(新浪) |
| `tool_get_lhb_stock_detail` | lhb | 个股某日龙虎榜席位明细，akshare(新浪) |
| `tool_get_zt_pool` | pool | 涨停股池（连板数/封板资金），akshare(东财) |
| `tool_get_strong_stocks` | pool | 强势股池（新高/量比），akshare(东财) |
| `tool_get_previous_zt` | pool | 昨日涨停今日表现，akshare(东财) |
| `tool_get_zbgc_pool` | pool | 炸板股池（冲板后开板），akshare(东财) |
| `tool_get_market_north_capital` | north_flow | 北向资金日频资金流（沪深股通），akshare(东财) |
| `tool_get_north_stock_hold` | north_flow | 北向资金持股明细，仅 tushare |
| `tool_get_margin` | margin | 融资融券汇总（按交易所），tushare+akshare(交易所) |
| `tool_get_margin_detail` | margin | 融资融券个股明细，tushare+akshare(上交所)+xueqiu |

### 已禁用接口（2 个）

| Tool | 原因 |
|------|------|
| `tool_get_earnings_forecast_history` | 依赖东财 stock_yjyg_em，无 provider 实现 |
| `tool_get_sector_capital_flow` | push2.eastmoney.com 域名不可达 |

## MCP 配置

```json
{
  "mcpServers": {
    "finance-data": {
      "command": "/Users/lianwu/ai/projects/FinanceData/.venv/bin/python",
      "args": ["/Users/lianwu/ai/projects/FinanceData/mcp_server.py"],
      "env": {
        "TUSHARE_TOKEN": "your_token"
      }
    }
  }
}
```
