# FinanceData

金融数据服务，支持 MCP（AI Agent）和 Python library 两种接入方式。47 个接口覆盖 14 个领域。

## Python Library 使用

```python
from finance_data import FinanceData

fd = FinanceData()

# 日线行情 → DataFrame
df = fd.kline_daily("000001", start="20260401", end="20260410").to_dataframe()

# 板块成分
members = fd.board_member("银行").to_dataframe()

# 实时行情
quote = fd.quote("000001")
print(quote.data[0]["price"])

# 异常处理
from finance_data import DataFetchError
try:
    fd.capital_flow("000001")
except DataFetchError as e:
    print(f"source={e.source}, kind={e.kind}")
```

## 配置

所有配置统一从项目根目录 `config.toml` 读取（唯一事实来源）。首次使用需复制模板：

```bash
cp config.toml.example config.toml
# 编辑 config.toml 填写 token 和 api_url
```

```toml
[tushare]
token = "your_token"
api_url = "http://your-proxy:8010/"
stock_minute_permission = false

[xueqiu]
cookie = ""  # 可选，空则自动获取
```

`config.toml` 已加入 `.gitignore`，不会提交到仓库。

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
client.py ─────→ service/<domain>.py → provider/<source>/<domain>/ → interface/<domain>/
(Python API)        (Dispatcher)          (数据源实现)                (Protocol + Model)
mcp/server.py ─→
(MCP 薄封装)
```

```
src/finance_data/
├── __init__.py         # 导出 FinanceData / DataResult / DataFetchError
├── client.py           # 统一 Python API 入口（FinanceData 类）
├── interface/          # 协议层：Protocol + dataclass models（含 to_dataframe()）
│   └── <domain>/       #   每个领域一个目录
│       └── history.py  #   Protocol 定义 + dataclass（含 to_dict()）
├── provider/           # 数据源实现（akshare/tushare/xueqiu/tencent）
│   ├── akshare/        #   无需 token，上游源：新浪/腾讯/同花顺/乐估/交易所
│   ├── tencent/        #   腾讯实时行情API（qt.gtimg.cn），无需token，65ms延迟
│   ├── tushare/        #   需 config.toml 中 tushare.token
│   ├── xueqiu/         #   海外可达，实时行情无需认证，K线需 cookie
│   └── symbol.py       #   跨 provider 股票代码转换
├── service/            # 业务编排层：Dispatcher 管理多 provider fallback 链
│   └── <domain>.py     #   每个领域一个 service
├── tool_specs/         # ToolSpec 统一注册表（CLI/HTTP/Health 自动派生）
│   └── registry.py
├── dashboard/          # 健康监控看板（FastAPI + React）
└── mcp/
    └── server.py       #   MCP tool 定义，调用 service 层
```

### Provider 优先级

`akshare`（无需 token）→ `tushare`（需 config.toml token）→ `xueqiu`（海外可达）

Service 层在模块加载时根据 config.toml 配置动态构建 provider 链：

```python
def _build_kline_history():
    providers = [AkshareKlineHistory()]          # 总是可用
    if has_tushare_token():                      # config.toml 有 token 才加入
        providers.append(TushareKlineHistory())
    if has_login_cookie():
        providers.append(XueqiuKlineHistory())   # 有 cookie 才加入
    return _KlineHistoryDispatcher(providers=providers)
```

### 东财接口与代理绕过

部分东财源（`_em` 后缀函数）必须绕过本地代理直连。`provider/akshare/_proxy.py` 提供 `ensure_eastmoney_no_proxy()`。新增东财源 provider 必须在模块顶部调用。

排查东财接口不可用时：先 `curl --noproxy '*'` 测试直连，再 `curl -x http://127.0.0.1:7890` 测试代理。

## MCP 配置

配置已从 config.toml 读取，MCP 无需注入环境变量：

```json
{
  "mcpServers": {
    "finance-data": {
      "command": "/Users/lianwu/ai/projects/FinanceData/.venv/bin/python",
      "args": ["/Users/lianwu/ai/projects/FinanceData/mcp_server.py"]
    }
  }
}
```
