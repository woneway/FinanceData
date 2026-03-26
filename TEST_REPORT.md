# Provider 集成测试报告

> 生成时间：2026-03-26 16:58:55
> 测试交易日：20260320

## 汇总：0 PASS / 38 FAIL / 1 SKIP（共 39 项）

| # | Tool | Provider | 状态 | 行数 | 耗时(s) | 备注 |
|---|------|----------|------|------|---------|------|
| 1 | `tool_get_stock_info` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='stock.xueqiu.com', port=443): Max retries exceeded with url: /v5/stock/f10/cn/company.json?symbol=SZ000001 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 2 | `tool_get_stock_info` | tushare | ❌ FAIL | 0 | 0.11 | [auth] 无效的 token |
| 3 | `tool_get_kline` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='web.ifzq.gtimg.cn', port=443): Max retries exceeded with url: /other/klineweb/klineWeb/weekTrends?code=sz000001&type=qfq&_var=trend_qfq&r=0.3506048543943414 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 4 | `tool_get_kline` | tushare | ❌ FAIL | 0 | 0.04 | [auth] 无效的 token |
| 5 | `tool_get_realtime_quote` | akshare | ❌ FAIL | 0 | 5.28 | [network] HTTPSConnectionPool(host='82.push2.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/clist/get?pn=1&pz=100&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f12&fs=m%3A0+t%3A6%2Cm%3A0+t%3A80%2Cm%3A1+t%3A2%2Cm%3A1+t%3A23%2Cm%3A0+t%3A81+s%3A2048&fields=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6%2Cf7%2Cf8%2Cf9%2Cf10%2Cf12%2Cf13%2Cf14%2Cf15%2Cf16%2Cf17%2Cf18%2Cf20%2Cf21%2Cf23%2Cf24%2Cf25%2Cf22%2Cf11%2Cf62%2Cf128%2Cf136%2Cf115%2Cf152 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 6 | `tool_get_realtime_quote` | tushare | ❌ FAIL | 0 | 0.05 | [auth] 无效的 token |
| 7 | `tool_get_index_quote` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPConnectionPool(host='127.0.0.1', port=7892): Max retries exceeded with url: http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCountSimple?node=hs_s (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 8 | `tool_get_index_quote` | tushare | ❌ FAIL | 0 | 0.05 | [auth] 无效的 token |
| 9 | `tool_get_index_history` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?secid=1.000001&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=101&fqt=0&beg=20250101&end=20250320 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 10 | `tool_get_index_history` | tushare | ❌ FAIL | 0 | 0.04 | [auth] 无效的 token |
| 11 | `tool_get_sector_rank` | akshare | ❌ FAIL | 0 | 5.13 | [data] 无数据 |
| 12 | `tool_get_chip_distribution` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?secid=0.000001&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61&klt=101&fqt=0&end=20260326&lmt=210 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 13 | `tool_get_chip_distribution` | tushare | ❌ FAIL | 0 | 0.00 | [data] 无数据: 000001 |
| 14 | `tool_get_financial_summary` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='quotes.sina.cn', port=443): Max retries exceeded with url: /cn/api/openapi.php/CompanyFinanceService.getFinanceReport2022?paperCode=sh000001&source=gjzb&type=0&page=1&num=1000 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 15 | `tool_get_financial_summary` | tushare | ❌ FAIL | 0 | 0.00 | [data] 无数据: 000001 |
| 16 | `tool_get_dividend` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='datacenter-web.eastmoney.com', port=443): Max retries exceeded with url: /api/data/v1/get?sortColumns=REPORT_DATE&sortTypes=-1&pageSize=500&pageNumber=1&reportName=RPT_SHAREBONUS_DET&columns=ALL&quoteColumns=&js=%7B%22data%22%3A%28x%29%2C%22pages%22%3A%28tp%29%7D&source=WEB&client=WEB&filter=%28SECURITY_CODE%3D%22000001%22%29 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 17 | `tool_get_dividend` | tushare | ❌ FAIL | 0 | 0.00 | [data] 无数据: 000001 |
| 18 | `tool_get_earnings_forecast` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='datacenter.eastmoney.com', port=443): Max retries exceeded with url: /securities/api/data/v1/get?sortColumns=NOTICE_DATE%2CSECURITY_CODE&sortTypes=-1%2C-1&pageSize=500&pageNumber=1&reportName=RPT_PUBLIC_OP_NEWPREDICT&columns=ALL&filter=+%28REPORT_DATE%3D%272026-03-31%27%29 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 19 | `tool_get_fund_flow` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/fflow/daykline/get?lmt=0&klt=101&secid=0.000001&fields1=f1%2Cf2%2Cf3%2Cf7&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf62%2Cf63%2Cf64%2Cf65&ut=b2884a393a59ad64002292a3e90d46a5&_=1774515535683 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 20 | `tool_get_trade_calendar` | tushare | ❌ FAIL | 0 | 0.00 | [data] 无数据: 20250101-20250331 |
| 21 | `tool_get_market_stats_realtime` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='legulegu.com', port=443): Max retries exceeded with url: /stockdata/market-activity (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 22 | `tool_get_lhb_detail` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='datacenter-web.eastmoney.com', port=443): Max retries exceeded with url: /api/data/v1/get?sortColumns=SECURITY_CODE%2CTRADE_DATE&sortTypes=1%2C-1&pageSize=5000&pageNumber=1&reportName=RPT_DAILYBILLBOARD_DETAILSNEW&columns=SECURITY_CODE%2CSECUCODE%2CSECURITY_NAME_ABBR%2CTRADE_DATE%2CEXPLAIN%2CCLOSE_PRICE%2CCHANGE_RATE%2CBILLBOARD_NET_AMT%2CBILLBOARD_BUY_AMT%2CBILLBOARD_SELL_AMT%2CBILLBOARD_DEAL_AMT%2CACCUM_AMOUNT%2CDEAL_NET_RATIO%2CDEAL_AMOUNT_RATIO%2CTURNOVERRATE%2CFREE_MARKET_CAP%2CEXPLANATION%2CD1_CLOSE_ADJCHRATE%2CD2_CLOSE_ADJCHRATE%2CD5_CLOSE_ADJCHRATE%2CD10_CLOSE_ADJCHRATE%2CSECURITY_TYPE_CODE&source=WEB&client=WEB&filter=%28TRADE_DATE%3C%3D%272026-03-20%27%29%28TRADE_DATE%3E%3D%272026-03-13%27%29 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 23 | `tool_get_lhb_detail` | tushare | ❌ FAIL | 0 | 0.00 | [data] 无数据: 20260320 |
| 24 | `tool_get_lhb_stock_stat` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='datacenter-web.eastmoney.com', port=443): Max retries exceeded with url: /api/data/v1/get?sortColumns=BILLBOARD_TIMES%2CLATEST_TDATE%2CSECURITY_CODE&sortTypes=-1%2C-1%2C1&pageSize=5000&pageNumber=1&reportName=RPT_BILLBOARD_TRADEALL&columns=ALL&source=WEB&client=WEB&filter=%28STATISTICS_CYCLE%3D%2201%22%29 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 25 | `tool_get_lhb_active_traders` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='datacenter-web.eastmoney.com', port=443): Max retries exceeded with url: /api/data/v1/get?sortColumns=TOTAL_NETAMT%2CONLIST_DATE%2COPERATEDEPT_CODE&sortTypes=-1%2C-1%2C1&pageSize=5000&pageNumber=1&reportName=RPT_OPERATEDEPT_ACTIVE&columns=ALL&source=WEB&client=WEB&filter=%28ONLIST_DATE%3E%3D%272026-03-13%27%29%28ONLIST_DATE%3C%3D%272026-03-20%27%29 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 26 | `tool_get_lhb_trader_stat` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='datacenter-web.eastmoney.com', port=443): Max retries exceeded with url: /api/data/v1/get?sortColumns=AMOUNT%2COPERATEDEPT_CODE&sortTypes=-1%2C1&pageSize=5000&pageNumber=1&reportName=RPT_OPERATEDEPT_LIST_STATISTICS&columns=ALL&source=WEB&client=WEB&filter=%28STATISTICSCYCLE%3D%2201%22%29 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 27 | `tool_get_lhb_stock_detail` | akshare | ⚠️ SKIP | 0 | 0.00 | [akshare] stock_lhb_detail_em 失败 (network): HTTPSConnectionPool(host='datacenter-web.eastmoney.com', port=443): Max retries exceeded with url: /api/data/v1/get?sortColumns=SECURITY_CODE%2CTRADE_DATE&sortTypes=1%2C-1&pageSize=5000&pageNumber=1&reportName=RPT_DAILYBILLBOARD_DETAILSNEW&columns=SECURITY_CODE%2CSECUCODE%2CSECURITY_NAME_ABBR%2CTRADE_DATE%2CEXPLAIN%2CCLOSE_PRICE%2CCHANGE_RATE%2CBILLBOARD_NET_AMT%2CBILLBOARD_BUY_AMT%2CBILLBOARD_SELL_AMT%2CBILLBOARD_DEAL_AMT%2CACCUM_AMOUNT%2CDEAL_NET_RATIO%2CDEAL_AMOUNT_RATIO%2CTURNOVERRATE%2CFREE_MARKET_CAP%2CEXPLANATION%2CD1_CLOSE_ADJCHRATE%2CD2_CLOSE_ADJCHRATE%2CD5_CLOSE_ADJCHRATE%2CD10_CLOSE_ADJCHRATE%2CSECURITY_TYPE_CODE&source=WEB&client=WEB&filter=%28TRADE_DATE%3C%3D%272026-03-20%27%29%28TRADE_DATE%3E%3D%272026-03-13%27%29 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 28 | `tool_get_zt_pool` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='push2ex.eastmoney.com', port=443): Max retries exceeded with url: /getTopicZTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=10000&sort=fbt%3Aasc&date=20260320 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 29 | `tool_get_strong_stocks` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='push2ex.eastmoney.com', port=443): Max retries exceeded with url: /getTopicQSPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=5000&sort=zdp%3Adesc&date=20260320 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 30 | `tool_get_previous_zt` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='push2ex.eastmoney.com', port=443): Max retries exceeded with url: /getYesterdayZTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=5000&sort=zs%3Adesc&date=20260320 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 31 | `tool_get_zbgc_pool` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='push2ex.eastmoney.com', port=443): Max retries exceeded with url: /getTopicZBPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=5000&sort=fbt%3Aasc&date=20260320 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 32 | `tool_get_north_flow` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='datacenter-web.eastmoney.com', port=443): Max retries exceeded with url: /api/data/v1/get?reportName=RPT_MUTUAL_QUOTA&columns=TRADE_DATE%2CMUTUAL_TYPE%2CBOARD_TYPE%2CMUTUAL_TYPE_NAME%2CFUNDS_DIRECTION%2CINDEX_CODE%2CINDEX_NAME%2CBOARD_CODE&quoteColumns=status~07~BOARD_CODE%2CdayNetAmtIn~07~BOARD_CODE%2CdayAmtRemain~07~BOARD_CODE%2CdayAmtThreshold~07~BOARD_CODE%2Cf104~07~BOARD_CODE%2Cf105~07~BOARD_CODE%2Cf106~07~BOARD_CODE%2Cf3~03~INDEX_CODE~INDEX_f3%2CnetBuyAmt~07~BOARD_CODE&quoteType=0&pageNumber=1&pageSize=2000&sortTypes=1&sortColumns=MUTUAL_TYPE&source=WEB&client=WEB (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 33 | `tool_get_north_stock_hold` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='data.eastmoney.com', port=443): Max retries exceeded with url: /hsgtcg/list.html (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 34 | `tool_get_north_stock_hold` | tushare | ❌ FAIL | 0 | 0.00 | [data] 无数据: symbol=600519 trade_date=20250320 |
| 35 | `tool_get_margin` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='query.sse.com.cn', port=443): Max retries exceeded with url: /marketdata/tradedata/queryMargin.do?isPagination=true&beginDate=20260320&endDate=20260320&tabType=&stockCode=&pageHelp.pageSize=5000&pageHelp.pageNo=1&pageHelp.beginPage=1&pageHelp.cacheSize=1&pageHelp.endPage=5 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 36 | `tool_get_margin` | tushare | ❌ FAIL | 0 | 0.00 | [data] 无数据: trade_date=20260320 |
| 37 | `tool_get_margin_detail` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='query.sse.com.cn', port=443): Max retries exceeded with url: /marketdata/tradedata/queryMargin.do?isPagination=true&tabType=mxtype&detailsDate=20260320&stockCode=&beginDate=&endDate=&pageHelp.pageSize=5000&pageHelp.pageCount=50&pageHelp.pageNo=1&pageHelp.beginPage=1&pageHelp.cacheSize=1&pageHelp.endPage=21 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |
| 38 | `tool_get_margin_detail` | tushare | ❌ FAIL | 0 | 0.00 | [data] 无数据: trade_date=20260320 |
| 39 | `tool_get_sector_fund_flow` | akshare | ❌ FAIL | 0 | 0.00 | [network] HTTPSConnectionPool(host='push2.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/clist/get?pn=1&pz=100&po=1&np=1&ut=b2884a393a59ad64002292a3e90d46a5&fltt=2&invt=2&fid0=f62&fs=m%3A90+t%3A2&stat=1&fields=f12%2Cf14%2Cf2%2Cf3%2Cf62%2Cf184%2Cf66%2Cf69%2Cf72%2Cf75%2Cf78%2Cf81%2Cf84%2Cf87%2Cf204%2Cf205%2Cf124&rt=52975239&_=1774515535700 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused"))) |

## 失败详情

### `tool_get_stock_info` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='stock.xueqiu.com', port=443): Max retries exceeded with url: /v5/stock/f10/cn/company.json?symbol=SZ000001 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_stock_info` (tushare)
- 错误：`[auth] 无效的 token`

### `tool_get_kline` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='web.ifzq.gtimg.cn', port=443): Max retries exceeded with url: /other/klineweb/klineWeb/weekTrends?code=sz000001&type=qfq&_var=trend_qfq&r=0.3506048543943414 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_kline` (tushare)
- 错误：`[auth] 无效的 token`

### `tool_get_realtime_quote` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='82.push2.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/clist/get?pn=1&pz=100&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f12&fs=m%3A0+t%3A6%2Cm%3A0+t%3A80%2Cm%3A1+t%3A2%2Cm%3A1+t%3A23%2Cm%3A0+t%3A81+s%3A2048&fields=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6%2Cf7%2Cf8%2Cf9%2Cf10%2Cf12%2Cf13%2Cf14%2Cf15%2Cf16%2Cf17%2Cf18%2Cf20%2Cf21%2Cf23%2Cf24%2Cf25%2Cf22%2Cf11%2Cf62%2Cf128%2Cf136%2Cf115%2Cf152 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_realtime_quote` (tushare)
- 错误：`[auth] 无效的 token`

### `tool_get_index_quote` (akshare)
- 错误：`[network] HTTPConnectionPool(host='127.0.0.1', port=7892): Max retries exceeded with url: http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCountSimple?node=hs_s (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_index_quote` (tushare)
- 错误：`[auth] 无效的 token`

### `tool_get_index_history` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?secid=1.000001&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58&klt=101&fqt=0&beg=20250101&end=20250320 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_index_history` (tushare)
- 错误：`[auth] 无效的 token`

### `tool_get_sector_rank` (akshare)
- 错误：`[data] 无数据`

### `tool_get_chip_distribution` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/kline/get?secid=0.000001&fields1=f1%2Cf2%2Cf3%2Cf4%2Cf5%2Cf6&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61&klt=101&fqt=0&end=20260326&lmt=210 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_chip_distribution` (tushare)
- 错误：`[data] 无数据: 000001`

### `tool_get_financial_summary` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='quotes.sina.cn', port=443): Max retries exceeded with url: /cn/api/openapi.php/CompanyFinanceService.getFinanceReport2022?paperCode=sh000001&source=gjzb&type=0&page=1&num=1000 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_financial_summary` (tushare)
- 错误：`[data] 无数据: 000001`

### `tool_get_dividend` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='datacenter-web.eastmoney.com', port=443): Max retries exceeded with url: /api/data/v1/get?sortColumns=REPORT_DATE&sortTypes=-1&pageSize=500&pageNumber=1&reportName=RPT_SHAREBONUS_DET&columns=ALL&quoteColumns=&js=%7B%22data%22%3A%28x%29%2C%22pages%22%3A%28tp%29%7D&source=WEB&client=WEB&filter=%28SECURITY_CODE%3D%22000001%22%29 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_dividend` (tushare)
- 错误：`[data] 无数据: 000001`

### `tool_get_earnings_forecast` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='datacenter.eastmoney.com', port=443): Max retries exceeded with url: /securities/api/data/v1/get?sortColumns=NOTICE_DATE%2CSECURITY_CODE&sortTypes=-1%2C-1&pageSize=500&pageNumber=1&reportName=RPT_PUBLIC_OP_NEWPREDICT&columns=ALL&filter=+%28REPORT_DATE%3D%272026-03-31%27%29 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_fund_flow` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/stock/fflow/daykline/get?lmt=0&klt=101&secid=0.000001&fields1=f1%2Cf2%2Cf3%2Cf7&fields2=f51%2Cf52%2Cf53%2Cf54%2Cf55%2Cf56%2Cf57%2Cf58%2Cf59%2Cf60%2Cf61%2Cf62%2Cf63%2Cf64%2Cf65&ut=b2884a393a59ad64002292a3e90d46a5&_=1774515535683 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_trade_calendar` (tushare)
- 错误：`[data] 无数据: 20250101-20250331`

### `tool_get_market_stats_realtime` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='legulegu.com', port=443): Max retries exceeded with url: /stockdata/market-activity (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_lhb_detail` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='datacenter-web.eastmoney.com', port=443): Max retries exceeded with url: /api/data/v1/get?sortColumns=SECURITY_CODE%2CTRADE_DATE&sortTypes=1%2C-1&pageSize=5000&pageNumber=1&reportName=RPT_DAILYBILLBOARD_DETAILSNEW&columns=SECURITY_CODE%2CSECUCODE%2CSECURITY_NAME_ABBR%2CTRADE_DATE%2CEXPLAIN%2CCLOSE_PRICE%2CCHANGE_RATE%2CBILLBOARD_NET_AMT%2CBILLBOARD_BUY_AMT%2CBILLBOARD_SELL_AMT%2CBILLBOARD_DEAL_AMT%2CACCUM_AMOUNT%2CDEAL_NET_RATIO%2CDEAL_AMOUNT_RATIO%2CTURNOVERRATE%2CFREE_MARKET_CAP%2CEXPLANATION%2CD1_CLOSE_ADJCHRATE%2CD2_CLOSE_ADJCHRATE%2CD5_CLOSE_ADJCHRATE%2CD10_CLOSE_ADJCHRATE%2CSECURITY_TYPE_CODE&source=WEB&client=WEB&filter=%28TRADE_DATE%3C%3D%272026-03-20%27%29%28TRADE_DATE%3E%3D%272026-03-13%27%29 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_lhb_detail` (tushare)
- 错误：`[data] 无数据: 20260320`

### `tool_get_lhb_stock_stat` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='datacenter-web.eastmoney.com', port=443): Max retries exceeded with url: /api/data/v1/get?sortColumns=BILLBOARD_TIMES%2CLATEST_TDATE%2CSECURITY_CODE&sortTypes=-1%2C-1%2C1&pageSize=5000&pageNumber=1&reportName=RPT_BILLBOARD_TRADEALL&columns=ALL&source=WEB&client=WEB&filter=%28STATISTICS_CYCLE%3D%2201%22%29 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_lhb_active_traders` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='datacenter-web.eastmoney.com', port=443): Max retries exceeded with url: /api/data/v1/get?sortColumns=TOTAL_NETAMT%2CONLIST_DATE%2COPERATEDEPT_CODE&sortTypes=-1%2C-1%2C1&pageSize=5000&pageNumber=1&reportName=RPT_OPERATEDEPT_ACTIVE&columns=ALL&source=WEB&client=WEB&filter=%28ONLIST_DATE%3E%3D%272026-03-13%27%29%28ONLIST_DATE%3C%3D%272026-03-20%27%29 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_lhb_trader_stat` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='datacenter-web.eastmoney.com', port=443): Max retries exceeded with url: /api/data/v1/get?sortColumns=AMOUNT%2COPERATEDEPT_CODE&sortTypes=-1%2C1&pageSize=5000&pageNumber=1&reportName=RPT_OPERATEDEPT_LIST_STATISTICS&columns=ALL&source=WEB&client=WEB&filter=%28STATISTICSCYCLE%3D%2201%22%29 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_zt_pool` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='push2ex.eastmoney.com', port=443): Max retries exceeded with url: /getTopicZTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=10000&sort=fbt%3Aasc&date=20260320 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_strong_stocks` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='push2ex.eastmoney.com', port=443): Max retries exceeded with url: /getTopicQSPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=5000&sort=zdp%3Adesc&date=20260320 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_previous_zt` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='push2ex.eastmoney.com', port=443): Max retries exceeded with url: /getYesterdayZTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=5000&sort=zs%3Adesc&date=20260320 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_zbgc_pool` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='push2ex.eastmoney.com', port=443): Max retries exceeded with url: /getTopicZBPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=5000&sort=fbt%3Aasc&date=20260320 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_north_flow` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='datacenter-web.eastmoney.com', port=443): Max retries exceeded with url: /api/data/v1/get?reportName=RPT_MUTUAL_QUOTA&columns=TRADE_DATE%2CMUTUAL_TYPE%2CBOARD_TYPE%2CMUTUAL_TYPE_NAME%2CFUNDS_DIRECTION%2CINDEX_CODE%2CINDEX_NAME%2CBOARD_CODE&quoteColumns=status~07~BOARD_CODE%2CdayNetAmtIn~07~BOARD_CODE%2CdayAmtRemain~07~BOARD_CODE%2CdayAmtThreshold~07~BOARD_CODE%2Cf104~07~BOARD_CODE%2Cf105~07~BOARD_CODE%2Cf106~07~BOARD_CODE%2Cf3~03~INDEX_CODE~INDEX_f3%2CnetBuyAmt~07~BOARD_CODE&quoteType=0&pageNumber=1&pageSize=2000&sortTypes=1&sortColumns=MUTUAL_TYPE&source=WEB&client=WEB (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_north_stock_hold` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='data.eastmoney.com', port=443): Max retries exceeded with url: /hsgtcg/list.html (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_north_stock_hold` (tushare)
- 错误：`[data] 无数据: symbol=600519 trade_date=20250320`

### `tool_get_margin` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='query.sse.com.cn', port=443): Max retries exceeded with url: /marketdata/tradedata/queryMargin.do?isPagination=true&beginDate=20260320&endDate=20260320&tabType=&stockCode=&pageHelp.pageSize=5000&pageHelp.pageNo=1&pageHelp.beginPage=1&pageHelp.cacheSize=1&pageHelp.endPage=5 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_margin` (tushare)
- 错误：`[data] 无数据: trade_date=20260320`

### `tool_get_margin_detail` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='query.sse.com.cn', port=443): Max retries exceeded with url: /marketdata/tradedata/queryMargin.do?isPagination=true&tabType=mxtype&detailsDate=20260320&stockCode=&beginDate=&endDate=&pageHelp.pageSize=5000&pageHelp.pageCount=50&pageHelp.pageNo=1&pageHelp.beginPage=1&pageHelp.cacheSize=1&pageHelp.endPage=21 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

### `tool_get_margin_detail` (tushare)
- 错误：`[data] 无数据: trade_date=20260320`

### `tool_get_sector_fund_flow` (akshare)
- 错误：`[network] HTTPSConnectionPool(host='push2.eastmoney.com', port=443): Max retries exceeded with url: /api/qt/clist/get?pn=1&pz=100&po=1&np=1&ut=b2884a393a59ad64002292a3e90d46a5&fltt=2&invt=2&fid0=f62&fs=m%3A90+t%3A2&stat=1&fields=f12%2Cf14%2Cf2%2Cf3%2Cf62%2Cf184%2Cf66%2Cf69%2Cf72%2Cf75%2Cf78%2Cf81%2Cf84%2Cf87%2Cf204%2Cf205%2Cf124&rt=52975239&_=1774515535700 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`

## 跳过详情

### `tool_get_lhb_stock_detail` (akshare)
- 原因：`[akshare] stock_lhb_detail_em 失败 (network): HTTPSConnectionPool(host='datacenter-web.eastmoney.com', port=443): Max retries exceeded with url: /api/data/v1/get?sortColumns=SECURITY_CODE%2CTRADE_DATE&sortTypes=1%2C-1&pageSize=5000&pageNumber=1&reportName=RPT_DAILYBILLBOARD_DETAILSNEW&columns=SECURITY_CODE%2CSECUCODE%2CSECURITY_NAME_ABBR%2CTRADE_DATE%2CEXPLAIN%2CCLOSE_PRICE%2CCHANGE_RATE%2CBILLBOARD_NET_AMT%2CBILLBOARD_BUY_AMT%2CBILLBOARD_SELL_AMT%2CBILLBOARD_DEAL_AMT%2CACCUM_AMOUNT%2CDEAL_NET_RATIO%2CDEAL_AMOUNT_RATIO%2CTURNOVERRATE%2CFREE_MARKET_CAP%2CEXPLANATION%2CD1_CLOSE_ADJCHRATE%2CD2_CLOSE_ADJCHRATE%2CD5_CLOSE_ADJCHRATE%2CD10_CLOSE_ADJCHRATE%2CSECURITY_TYPE_CODE&source=WEB&client=WEB&filter=%28TRADE_DATE%3C%3D%272026-03-20%27%29%28TRADE_DATE%3E%3D%272026-03-13%27%29 (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=7892): Failed to establish a new connection: [Errno 61] Connection refused")))`
