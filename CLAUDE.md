# FinanceData

金融数据服务，支持 MCP（AI Agent）和 Python library 两种接入方式。48 个接口覆盖 14 个领域。

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

[cache]
enabled = true  # DuckDB 缓存开关；false 等价于历史的 FINANCE_DATA_CACHE=0

[proxy]
no_proxy_hosts = ["eastmoney.com", ".eastmoney.com"]  # 必须绕代理直连的 hosts
```

`config.toml` 已加入 `.gitignore`，不会提交到仓库。

**Breaking 迁移指引**（自 cleanup-config-and-proxy-leftovers 起）：
- `FINANCE_DATA_CACHE=0` 环境变量不再生效，改用 `[cache] enabled = false`
- `_proxy.py` 内不再硬编码 hosts，改读 `[proxy] no_proxy_hosts`，缺省自动含东财域名

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
│   └── registry/       #   按 domain 拆分的 ToolSpec 子模块（合计 48 个 ToolSpec）
│       ├── __init__.py #     按 _DOMAIN_ORDER 拼接为 TOOL_SPEC_REGISTRY OrderedDict
│       ├── _factories.py  #   _param/_provider/_service/_probe/_meta 工厂 helper
│       └── <domain>.py × 14
├── dashboard/          # 健康监控看板（FastAPI + React）
└── mcp/
    ├── _app.py         #   FastMCP 单例 mcp + helpers (_to_json / _invoke_tool_json)
    ├── tools/          #   按 domain 拆分的 @mcp.tool 函数（合计 48 个 MCP tool）
    │   └── <domain>.py × 14
    └── server.py       #   aggregator：触发 tools 注册 + re-export service 与 tool 函数
```

> **拆分约束**（由 `tests/mcp/test_tools_layout.py` 守护）：
> - `mcp/tools/<domain>.py` 中函数顺序 = `tool_specs/registry/<domain>.py` 中 SPECS 顺序
> - `mcp/server.py` 中 14 个 tools 子模块 import 顺序 = `tool_specs/registry/__init__.py` 中 `_DOMAIN_ORDER` 顺序
> - 任一新增 / 重命名 tool 必须同时改 `mcp/tools/<domain>.py` + `tool_specs/registry/<domain>.py` 同 domain

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

## OpenSpec 流程

本项目所有结构性变更必须走 OpenSpec change，禁止直接 commit feature。OpenSpec 与 `.claude/skills/tool-acceptance` 是同一验收流程的两种描述：前者负责制品归档，后者负责逐层验收执行；最终产物都汇聚到 `acceptance.md`。

四个阶段对应纪律（详见 `openspec/config.yaml` rules 段）：

| 阶段 | 命令 | 必做事项 |
|---|---|---|
| Propose | `openspec new change <slug>` | 写 proposal、specs 增量、design、tasks；涉及新数据源时同步起草 upstream-alignment.md |
| Apply | 按 tasks.md 顺序实现 | 按序执行任务、每组任务跑相关测试；遵循 `.claude/rules/finance-coding.md` 的「接口对接铁律」；偏离 spec 时先同步 markdown |
| Verify | 运行 tool-acceptance skill | 写 acceptance.md（Completeness/Correctness/Coherence + 三类风险显式列出） |
| Archive | `openspec archive <slug>` | 必须有 acceptance.md；涉及新数据源必须有 upstream-alignment.md；spec delta 必须与现网代码一致 |

模板路径：

- `openspec/templates/acceptance.template.md`
- `openspec/templates/upstream-alignment.template.md`

### 新加一个接口的标准流程（8 步）

1. `openspec new change <slug>` 生成脚手架
2. 用 `openspec/templates/upstream-alignment.template.md` 起草 upstream-alignment.md：定位官方文档、真实调用 API、确认字段 / 单位 / 更新时效
3. 写 spec delta：行为契约 + Given/When/Then，挂到合适 spec（如 `kline-history`）
4. 写 design：source-of-truth 映射表（provider × 参数 → 上游接口）
5. 写 tasks：每条追溯 requirement，含正常 / 边界 / 后台可见性 / 回归 / 文档
6. 实现：在 `mcp/tools/<domain>.py` 加 ToolSpec + `@mcp.tool`，service 层加方法，provider 加适配；东财 akshare 必须调 `ensure_eastmoney_no_proxy()`
7. 跑 pytest + tool-acceptance skill 逐层（provider / service / CLI / HTTP / MCP / Web）
8. 用 `openspec/templates/acceptance.template.md` 写 acceptance.md → `openspec archive <slug>`

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
