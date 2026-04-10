# Tencent API Notes

## 定位

本文件是 FinanceData 项目内的 Tencent 接口文档。

- 目标：记录本项目实际使用的腾讯行情接口、字段语义、验证方法和当前验证状态
- 性质：项目内接口文档，不是腾讯官方文档
- 约束：只有经过实际调用验证的内容才写入本文件

## 资料来源

- 实际接口入口：`http://qt.gtimg.cn/q=sz000001`
- 项目实现：[src/finance_data/provider/tencent/client.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/tencent/client.py)
- 辅助资料：
  - `https://xhto.cn/archives/162.html`
  - `https://blog.csdn.net/geofferysun/article/details/114386084`

说明：

- 当前未找到稳定的腾讯官方公开股票 API 文档
- 本项目以“实际返回 + 项目字段映射”为真相源
- 第三方网页仅用于辅助理解字段索引

## 接口目录

本项目当前实际使用并已验证的原始接口只有一个：

- `qt.gtimg.cn/q=<symbol>`

该接口当前已验证可支撑：

- 股票实时快照
- `TencentDailyBasic.get_daily_basic`
- `TencentLimitPrice.get_limit_price`

## 接口定义

### 1. 股票实时主接口

- Endpoint：`http://qt.gtimg.cn/q=<symbol>`
- 请求方法：`GET`
- symbol 格式：腾讯格式，如 `sz000001`、`sh600519`
- 本项目转换函数：[src/finance_data/provider/symbol.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/symbol.py)
  - `to_tencent("000001") -> "sz000001"`

### 返回格式

- 响应是 `GBK` 编码文本
- 主体格式类似：

```text
v_sz000001="51~平安银行~000001~11.10~11.22~..."
```

- 字段以 `~` 分隔
- 本项目字段索引表定义在：
  [src/finance_data/provider/tencent/client.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/tencent/client.py)

本项目当前已使用并验证的核心字段：

- `1`: `name`
- `2`: `code`
- `3`: `current`
- `4`: `prev_close`
- `32`: `pct_change`
- `36`: `volume_hand`
- `37`: `amount_wan`
- `38`: `turnover_rate`
- `39`: `pe`
- `44`: `market_cap`
- `46`: `pb`
- `47`: `limit_up`
- `48`: `limit_down`
- `30`: `datetime`

### 实际验证结果

验证日期：`2026-04-09`

股票实时原始请求：

```bash
curl -s 'http://qt.gtimg.cn/q=sz000001'
```

验证结果：

- 调用成功
- 返回非空文本
- 返回结构符合 `v_sz000001="...~...~..."` 形式

项目实现验证：

```python
from finance_data.provider.tencent.client import fetch_quote
q = fetch_quote("000001")
```

验证结果：

- `code=000001`
- `name=平安银行`
- `current=11.1`
- `prev_close=11.22`
- `limit_up=12.34`
- `limit_down=10.1`
- `pe=5.05`
- `pb=0.48`
- `market_cap=215402000000.0`
- `datetime=20260409161409`

结论：

- 股票实时：已验证通过

### 本项目标准化规则

定义位置：
[src/finance_data/provider/tencent/client.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/tencent/client.py)

标准化规则：

- `volume_hand` 手 -> `volume` 股，乘以 `100`
- `amount_wan` 万元 -> `amount` 元，乘以 `10000`
- `market_cap` 亿元 -> 元，乘以 `1e8`

## 本项目对应能力

### `TencentDailyBasic`

- 文件：[src/finance_data/provider/tencent/daily_basic.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/tencent/daily_basic.py)
- 使用字段：
  - `code`
  - `name`
  - `datetime`
  - `pe`
  - `pb`
  - `market_cap`
  - `circ_market_cap`
  - `turnover_rate`
  - `volume_ratio`

### `TencentLimitPrice`

- 文件：[src/finance_data/provider/tencent/limit_price.py](/Users/lianwu/ai/projects/FinanceData/src/finance_data/provider/tencent/limit_price.py)
- 使用字段：
  - `code`
  - `name`
  - `datetime`
  - `limit_up`
  - `limit_down`
  - `prev_close`
  - `current`

## 已知限制

- 无稳定官方公开文档，字段语义依赖实际返回和社区资料
- 返回为位置字段，不是 JSON，对字段顺序变化敏感
- 当前文档只覆盖本项目已使用字段，未覆盖全部字段
