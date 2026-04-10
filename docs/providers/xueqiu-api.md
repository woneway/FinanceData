# Xueqiu API Notes

## 定位

本文件是 FinanceData 项目内的 Xueqiu 接口文档。

- 目标：记录本项目实际使用的雪球接口、参数、返回结构、验证方法和当前验证状态
- 性质：项目内接口文档，不是雪球官方文档
- 约束：只有经过实际调用验证的内容才写入本文件

## 资料来源

- 项目实现：
  - [src/finance_data/provider/xueqiu/client.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/client.py)
  - [src/finance_data/provider/xueqiu/realtime/realtime.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/realtime/realtime.py)
  - [src/finance_data/provider/xueqiu/kline/history.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/kline/history.py)
  - [src/finance_data/provider/xueqiu/stock/history.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/stock/history.py)
  - [src/finance_data/provider/xueqiu/fundamental/history.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/fundamental/history.py)
  - [src/finance_data/provider/xueqiu/cashflow/realtime.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/cashflow/realtime.py)
  - [src/finance_data/provider/xueqiu/margin/history.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/margin/history.py)
- GitHub 参考：
  - `https://github.com/1dot75cm/xueqiu`
  - `https://github.com/1dot75cm/xueqiu/blob/master/xueqiu/api.py`
  - `https://github.com/bellchet58/xueqiu-api`
- 辅助资料：
  - `https://blog.csdn.net/qq_31856061/article/details/127319805`

说明：

- 当前未找到稳定公开的雪球官方股票 API 文档入口
- 本项目以“实际 endpoint + 实际响应”为真相源
- GitHub 封装项目和第三方网页只用于辅助确认参数和字段

## 认证与访问方式

共享访问逻辑定义在：
[src/finance_data/provider/xueqiu/client.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/client.py)

当前项目支持 4 层 cookie 获取：

1. `XUEQIU_COOKIE` 环境变量
2. 浏览器自动提取
3. 文件缓存
4. 访客 cookie

验证结果表明：

- 部分 endpoint 可在当前会话下直接访问
- `quotec`、`company`、`indicator`、`bonus`、`assort`、`margin`、`kline` 均已完成实际调用验证
- 是否必须登录 cookie，仍应以各具体接口的当前行为为准，不假设长期稳定

## 接口目录

本项目当前已接入并验证的 endpoint：

- `GET /v5/stock/realtime/quotec.json`
- `GET /v5/stock/chart/kline.json`
- `GET /v5/stock/f10/cn/company.json`
- `GET /v5/stock/finance/cn/indicator.json`
- `GET /v5/stock/f10/cn/bonus.json`
- `GET /v5/stock/capital/assort.json`
- `GET /v5/stock/capital/margin.json`

## 接口定义

### 1. 股票实时 / 大盘实时

- Endpoint：`https://stock.xueqiu.com/v5/stock/realtime/quotec.json`
- 参数：
  - `symbol`，如 `SZ000001`
- 本项目使用：
  - 个股实时：[src/finance_data/provider/xueqiu/realtime/realtime.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/realtime/realtime.py)
  - 指数实时：[src/finance_data/provider/xueqiu/index/realtime.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/index/realtime.py)

已验证关键字段：

- `symbol`
- `current`
- `percent`
- `chg`
- `timestamp`
- `volume`
- `amount`
- `market_capital`
- `turnover_rate`
- `open`
- `last_close`
- `high`
- `low`

### 实际验证结果

验证日期：`2026-04-09`

原始请求验证：

```python
from finance_data.provider.xueqiu.client import get_session
s = get_session()
r = s.get(
    "https://stock.xueqiu.com/v5/stock/realtime/quotec.json",
    params={"symbol": "SZ000001"},
    timeout=15,
)
```

验证结果：

- `HTTP 200`
- `data` 类型为 `list`
- 首项已验证字段包括：
  - `symbol`
  - `current`
  - `percent`
  - `chg`
  - `timestamp`
  - `volume`
  - `amount`
  - `market_capital`
  - `turnover_rate`
  - `open`
  - `last_close`
  - `high`
  - `low`

结论：

- 股票实时：已验证通过
- 大盘实时：本项目当前也复用该 endpoint，已验证通过

### 2. K 线

- Endpoint：`https://stock.xueqiu.com/v5/stock/chart/kline.json`
- 参数：
  - `symbol`
  - `begin`
  - `period`
  - `type`
  - `count`
  - `indicator`
- 本项目使用：
  - 个股 K 线：[src/finance_data/provider/xueqiu/kline/history.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/kline/history.py)
  - 指数 K 线：[src/finance_data/provider/xueqiu/index/history.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/index/history.py)

已验证返回结构：

        - `data.symbol`
        - `data.column`
        - `data.item`

### 3. 公司信息

- Endpoint：`https://stock.xueqiu.com/v5/stock/f10/cn/company.json`
- 参数：
  - `symbol`
- 本项目使用：
  - [src/finance_data/provider/xueqiu/stock/history.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/stock/history.py)

已验证返回结构：

- `data.company`

### 4. 财务指标

- Endpoint：`https://stock.xueqiu.com/v5/stock/finance/cn/indicator.json`
- 参数：
  - `symbol`
  - `type`
  - `is_detail`
  - `count`
- 本项目使用：
  - [src/finance_data/provider/xueqiu/fundamental/history.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/fundamental/history.py)

已验证返回结构：

- `data.currency`
- `data.currency_name`
- `data.last_report_name`
- `data.list`

### 5. 分红记录

- Endpoint：`https://stock.xueqiu.com/v5/stock/f10/cn/bonus.json`
- 参数：
  - `symbol`
  - `size`
  - `page`
- 本项目使用：
  - [src/finance_data/provider/xueqiu/fundamental/history.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/fundamental/history.py)

已验证返回结构：

- `data.items`
- `data.allots`
- `data.addtions`

### 6. 资金流向

- Endpoint：`https://stock.xueqiu.com/v5/stock/capital/assort.json`
- 参数：
  - `symbol`
- 本项目使用：
  - [src/finance_data/provider/xueqiu/cashflow/realtime.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/cashflow/realtime.py)

已验证关键字段：

- `buy_total`
- `sell_total`
- `buy_large`
- `sell_large`
- `buy_xlarge`
- `sell_xlarge`
- `timestamp`

### 7. 融资融券

- Endpoint：`https://stock.xueqiu.com/v5/stock/capital/margin.json`
- 参数：
  - `symbol`
  - `count`
- 本项目使用：
  - [src/finance_data/provider/xueqiu/margin/history.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/xueqiu/margin/history.py)

已验证返回结构：

- `data.inclusion_date`
- `data.items`

## 实际验证记录

验证日期：`2026-04-09`

### 原始 endpoint 验证

以下 endpoint 已完成实际调用，并返回 `HTTP 200`：

- `quotec.json`
- `kline.json`
- `company.json`
- `indicator.json`
- `bonus.json`
- `assort.json`
- `margin.json`

关键验证结果：

- `quotec.json`
  - 返回 `data: list`
  - 首项包含 `symbol/current/percent/timestamp/volume/amount/...`
- `kline.json`
  - 返回 `data.symbol/data.column/data.item`
  - 验证结果：`24` 个 columns，`5` 条 items
- `company.json`
  - 返回 `data.company`
- `indicator.json`
  - 返回 `data.list`
- `bonus.json`
  - 返回 `data.items`
- `assort.json`
  - 返回资金流向字段字典
- `margin.json`
  - 返回 `data.items`

### 本项目 provider 验证

以下 provider 已完成实际调用验证：

- `XueqiuRealtimeQuote`
- `XueqiuKlineHistory`
- `XueqiuStockHistory`
- `XueqiuFinancialSummary`
- `XueqiuDividend`
- `XueqiuStockCapitalFlow`
- `XueqiuMarginDetail`

验证结果摘要：

- `stock`: 成功返回数据
- `fundamental`: 返回 `20` 条记录
- `dividend`: 返回 `28` 条记录
- `cashflow`: 成功返回数据
- `margin`: 返回 `10` 条记录

## 已知限制

- 当前没有稳定公开官方文档，长期字段稳定性无法由官方保证
- 部分接口是否要求登录 cookie，可能随雪球策略调整而变化
- 本文件只覆盖项目当前已接入并已验证的 endpoint，不覆盖全部雪球接口
