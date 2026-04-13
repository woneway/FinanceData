# Provider 集成测试报告

> 生成时间：2026-04-13 21:30:42
> 测试交易日：20260410

## 汇总：0 PASS / 22 FAIL / 0 SKIP（共 22 项）

| # | Tool | Provider | 状态 | 行数 | 耗时(s) | 备注 |
|---|------|----------|------|------|---------|------|
| 1 | `tool_get_stock_info` | tushare | ❌ FAIL | 0 | 0.16 | [auth] 您的token不对，请确认。 |
| 2 | `tool_get_kline` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='web.ifzq.gtimg.cn', port=443): Max retries exceeded with url: /other/klineweb/klineWeb/weekTrends?code=sz000001&type=qfq&_var=trend_qfq&r=0.3506048543943414 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 3 | `tool_get_kline` | tushare | ❌ FAIL | 0 | 0.14 | [auth] 您的token不对，请确认。 |
| 4 | `tool_get_quote_realtime` | tushare | ❌ FAIL | 0 | 0.03 | [auth] 您的token不对，请确认。 |
| 5 | `tool_get_index_quote` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPConnectionPool(host='127.0.0.1', port=7892): Max retries exceeded with url: http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCountSimple?node=hs_s (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 6 | `tool_get_index_quote` | tushare | ❌ FAIL | 0 | 0.03 | [auth] 您的token不对，请确认。 |
| 7 | `tool_get_index_kline_history` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='finance.sina.com.cn', port=443): Max retries exceeded with url: /realstock/company/sh000001/hisdata/klc_kl.js?d=2020_2_4 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 8 | `tool_get_index_kline_history` | tushare | ❌ FAIL | 0 | 0.03 | [auth] 您的token不对，请确认。 |
| 9 | `tool_get_board_index_history` | tushare | ❌ FAIL | 0 | 0.14 | [auth] 您的token不对，请确认。 |
| 10 | `tool_get_chip_distribution` | tushare | ❌ FAIL | 0 | 0.12 | [auth] 您的token不对，请确认。 |
| 11 | `tool_get_financial_summary` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='quotes.sina.cn', port=443): Max retries exceeded with url: /cn/api/openapi.php/CompanyFinanceService.getFinanceReport2022?paperCode=sh000001&source=gjzb&type=0&page=1&num=1000 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 12 | `tool_get_financial_summary` | tushare | ❌ FAIL | 0 | 0.03 | [auth] 您的token不对，请确认。 |
| 13 | `tool_get_dividend` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='basic.10jqka.com.cn', port=443): Max retries exceeded with url: /new/000001/bonus.html (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 14 | `tool_get_dividend` | tushare | ❌ FAIL | 0 | 0.09 | [auth] 您的token不对，请确认。 |
| 15 | `tool_get_trade_calendar` | tushare | ❌ FAIL | 0 | 0.14 | [auth] 您的token不对，请确认。 |
| 16 | `tool_get_market_stats_realtime` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='legulegu.com', port=443): Max retries exceeded with url: /stockdata/market-activity (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 17 | `tool_get_lhb_detail_history` | tushare | ❌ FAIL | 0 | 0.11 | [auth] 您的token不对，请确认。 |
| 18 | `tool_get_north_hold_daily` | tushare | ❌ FAIL | 0 | 0.14 | [auth] 您的token不对，请确认。 |
| 19 | `tool_get_margin_history` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='query.sse.com.cn', port=443): Max retries exceeded with url: /marketdata/tradedata/queryMargin.do?isPagination=true&beginDate=20260410&endDate=20260410&tabType=&stockCode=&pageHelp.pageSize=5000&pageHelp.pageNo=1&pageHelp.beginPage=1&pageHelp.cacheSize=1&pageHelp.endPage=5 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 20 | `tool_get_margin_history` | tushare | ❌ FAIL | 0 | 0.03 | [auth] 您的token不对，请确认。 |
| 21 | `tool_get_margin_detail_history` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='query.sse.com.cn', port=443): Max retries exceeded with url: /marketdata/tradedata/queryMargin.do?isPagination=true&tabType=mxtype&detailsDate=20260410&stockCode=&beginDate=&endDate=&pageHelp.pageSize=5000&pageHelp.pageCount=50&pageHelp.pageNo=1&pageHelp.beginPage=1&pageHelp.cacheSize=1&pageHelp.endPage=21 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 22 | `tool_get_margin_detail_history` | tushare | ❌ FAIL | 0 | 0.07 | [auth] 您的token不对，请确认。 |

## 失败详情

### `tool_get_stock_info` (tushare)
- 错误：`[auth] 您的token不对，请确认。`

### `tool_get_kline` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='web.ifzq.gtimg.cn', port=443): Max retries exceeded with url: /other/klineweb/klineWeb/weekTrends?code=sz000001&type=qfq&_var=trend_qfq&r=0.3506048543943414 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_kline` (tushare)
- 错误：`[auth] 您的token不对，请确认。`

### `tool_get_quote_realtime` (tushare)
- 错误：`[auth] 您的token不对，请确认。`

### `tool_get_index_quote` (akshare)
- 错误：`[network] HTTPConnectionPool(host='127.0.0.1', port=7892): Max retries exceeded with url: http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCountSimple?node=hs_s (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_index_quote` (tushare)
- 错误：`[auth] 您的token不对，请确认。`

### `tool_get_index_kline_history` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='finance.sina.com.cn', port=443): Max retries exceeded with url: /realstock/company/sh000001/hisdata/klc_kl.js?d=2020_2_4 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_index_kline_history` (tushare)
- 错误：`[auth] 您的token不对，请确认。`

### `tool_get_board_index_history` (tushare)
- 错误：`[auth] 您的token不对，请确认。`

### `tool_get_chip_distribution` (tushare)
- 错误：`[auth] 您的token不对，请确认。`

### `tool_get_financial_summary` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='quotes.sina.cn', port=443): Max retries exceeded with url: /cn/api/openapi.php/CompanyFinanceService.getFinanceReport2022?paperCode=sh000001&source=gjzb&type=0&page=1&num=1000 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_financial_summary` (tushare)
- 错误：`[auth] 您的token不对，请确认。`

### `tool_get_dividend` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='basic.10jqka.com.cn', port=443): Max retries exceeded with url: /new/000001/bonus.html (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_dividend` (tushare)
- 错误：`[auth] 您的token不对，请确认。`

### `tool_get_trade_calendar` (tushare)
- 错误：`[auth] 您的token不对，请确认。`

### `tool_get_market_stats_realtime` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='legulegu.com', port=443): Max retries exceeded with url: /stockdata/market-activity (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_lhb_detail_history` (tushare)
- 错误：`[auth] 您的token不对，请确认。`

### `tool_get_north_hold_daily` (tushare)
- 错误：`[auth] 您的token不对，请确认。`

### `tool_get_margin_history` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='query.sse.com.cn', port=443): Max retries exceeded with url: /marketdata/tradedata/queryMargin.do?isPagination=true&beginDate=20260410&endDate=20260410&tabType=&stockCode=&pageHelp.pageSize=5000&pageHelp.pageNo=1&pageHelp.beginPage=1&pageHelp.cacheSize=1&pageHelp.endPage=5 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_margin_history` (tushare)
- 错误：`[auth] 您的token不对，请确认。`

### `tool_get_margin_detail_history` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='query.sse.com.cn', port=443): Max retries exceeded with url: /marketdata/tradedata/queryMargin.do?isPagination=true&tabType=mxtype&detailsDate=20260410&stockCode=&beginDate=&endDate=&pageHelp.pageSize=5000&pageHelp.pageCount=50&pageHelp.pageNo=1&pageHelp.beginPage=1&pageHelp.cacheSize=1&pageHelp.endPage=21 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_margin_detail_history` (tushare)
- 错误：`[auth] 您的token不对，请确认。`

## 跳过详情

_无跳过项_
