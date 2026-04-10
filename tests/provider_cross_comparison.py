"""
跨 Provider 数据对比测试

测试所有支持多 provider 的接口，对比返回数据的:
1. 字段结构一致性
2. 数值合理性 (同日期/同股票)
3. 单位一致性 (volume=股, amount=元)

运行: INTEGRATION_PROXY=http://127.0.0.1:7890 .venv/bin/python tests/provider_cross_comparison.py
"""
import os
import sys
import datetime
import traceback

# 代理注入
_CLASH_PROXY = os.environ.get("INTEGRATION_PROXY", "http://127.0.0.1:7890")
_PROXY_ENABLED = os.environ.get("NO_PROXY_INJECT", "").strip().lower() not in ("1", "true", "yes")

if _PROXY_ENABLED:
    import requests as _req
    _orig_init = _req.Session.__init__

    def _proxied_init(self, *a, **kw):
        _orig_init(self, *a, **kw)
        self.proxies = {"http": _CLASH_PROXY, "https": _CLASH_PROXY}

    _req.Session.__init__ = _proxied_init
    print(f"[proxy] 注入 → {_CLASH_PROXY}")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

results = []

def run_test(name, fn, *args, **kwargs):
    """执行单个测试，记录结果。"""
    try:
        result = fn(*args, **kwargs)
        return result, None
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:100]}"


def compare_fields(name, data1, data2, provider1_name, provider2_name):
    """对比两个 provider 的字段结构。"""
    if not data1 or not data2:
        return []

    issues = []
    keys1 = set(data1[0].keys()) if data1 else set()
    keys2 = set(data2[0].keys()) if data2 else set()

    only_in_1 = keys1 - keys2
    only_in_2 = keys2 - keys1

    if only_in_1:
        issues.append(f"{provider1_name} 独有字段: {only_in_1}")
    if only_in_2:
        issues.append(f"{provider2_name} 独有字段: {only_in_2}")

    return issues


def compare_kline_values(name, ak_data, xq_data, symbol):
    """对比 kline 数据值。"""
    issues = []

    # 按日期索引数据
    ak_by_date = {bar['date']: bar for bar in ak_data}
    xq_by_date = {bar['date']: bar for bar in xq_data}

    common_dates = set(ak_by_date.keys()) & set(xq_by_date.keys())

    for date in sorted(common_dates)[:5]:  # 只比较前5天
        ak = ak_by_date[date]
        xq = xq_by_date[date]

        # 比较收盘价 (允许小误差)
        ak_close = ak.get('close', 0)
        xq_close = xq.get('close', 0)
        if ak_close and xq_close:
            diff_pct = abs(ak_close - xq_close) / xq_close * 100
            if diff_pct > 2:  # 超过2%差异
                issues.append(f"{date} close差异大: akshare={ak_close}, xueqiu={xq_close}, diff={diff_pct:.1f}%")

        # 比较 volume (这个会有大差异，因为计算方式不同)
        ak_vol = ak.get('volume', 0)
        xq_vol = xq.get('volume', 0)
        if ak_vol and xq_vol:
            vol_ratio = ak_vol / xq_vol if xq_vol else 0
            # 如果比例不是接近10(手/股)或1:1，标记
            if not (0.8 < vol_ratio < 1.2 or 8 < vol_ratio < 12):
                issues.append(f"{date} volume比例异常: akshare={ak_vol:,.0f}, xueqiu={xq_vol:,.0f}, ratio={vol_ratio:.2f}")

    return issues


# ==================== 测试用例 ====================

def test_kline_comparison():
    """对比 akshare 和 xueqiu 的 K线数据。"""
    print("\n" + "="*60)
    print("  KLINE 对比测试 (akshare vs xueqiu)")
    print("="*60)

    from finance_data.provider.akshare.kline.history import AkshareKlineHistory
    from finance_data.provider.xueqiu.kline.history import XueqiuKlineHistory

    symbol = "000001"
    start = "20250106"
    end = "20250110"

    ak = AkshareKlineHistory()
    xq = XueqiuKlineHistory()

    # 获取数据
    ak_result, ak_err = run_test("akshare kline", ak.get_kline_history, symbol, "daily", start, end, "qfq")
    xq_result, xq_err = run_test("xueqiu kline", xq.get_kline_history, symbol, "daily", start, end)

    if ak_err:
        print(f"  akshare ERROR: {ak_err}")
    if xq_err:
        print(f"  xueqiu ERROR: {xq_err}")

    if ak_result:
        print(f"  akshare: {len(ak_result.data)} rows")
        for bar in ak_result.data[:3]:
            print(f"    {bar['date']}: close={bar['close']}, volume={bar['volume']:,}, amount={bar['amount']:,.0f}")

    if xq_result:
        print(f"  xueqiu: {len(xq_result.data)} rows")
        # xueqiu 返回的数据可能跨越更长时间，需要按日期过滤
        xq_filtered = [b for b in xq_result.data if start <= b['date'] <= end]
        print(f"  xueqiu (filtered {start}-{end}): {len(xq_filtered)} rows")
        for bar in xq_filtered[:3]:
            print(f"    {bar['date']}: close={bar['close']}, volume={bar['volume']:,}, amount={bar['amount']:,.0f}")

    # 字段对比
    if ak_result and xq_result:
        xq_filtered = [b for b in xq_result.data if start <= b['date'] <= end]
        field_issues = compare_fields("kline", ak_result.data, xq_filtered, "akshare", "xueqiu")
        if field_issues:
            for issue in field_issues:
                print(f"  {RED}FIELD ISSUE:{RESET} {issue}")
        else:
            print(f"  {GREEN}字段结构一致{RESET}")

        # 数值对比
        value_issues = compare_kline_values("kline", ak_result.data, xq_filtered, symbol)
        if value_issues:
            for issue in value_issues:
                print(f"  {RED}VALUE ISSUE:{RESET} {issue}")
        else:
            print(f"  {GREEN}数值对比正常{RESET}")

    # 记录结果
    results.append({
        "test": "kline_comparison",
        "akshare": "PASS" if ak_result else "FAIL",
        "xueqiu": "PASS" if xq_result else "FAIL",
    })


def test_realtime_comparison():
    """对比 akshare 和 xueqiu 的实时行情。"""
    print("\n" + "="*60)
    print("  REALTIME 对比测试 (akshare vs xueqiu)")
    print("="*60)

    from finance_data.provider.akshare.realtime.realtime import AkshareRealtimeQuote
    from finance_data.provider.xueqiu.realtime.realtime import XueqiuRealtimeQuote

    symbol = "000001"

    ak = AkshareRealtimeQuote()
    xq = XueqiuRealtimeQuote()

    ak_result, ak_err = run_test("akshare realtime", ak.get_realtime_quote, symbol)
    xq_result, xq_err = run_test("xueqiu realtime", xq.get_realtime_quote, symbol)

    if ak_err:
        print(f"  akshare ERROR: {ak_err}")
    if xq_err:
        print(f"  xueqiu ERROR: {xq_err}")

    if ak_result and ak_result.data:
        print(f"  akshare: {len(ak_result.data)} rows")
        print(f"    {ak_result.data[0]}")

    if xq_result and xq_result.data:
        print(f"  xueqiu: {len(xq_result.data)} rows")
        print(f"    {xq_result.data[0]}")

    results.append({
        "test": "realtime_comparison",
        "akshare": "PASS" if ak_result else "FAIL",
        "xueqiu": "PASS" if xq_result else "FAIL",
    })


def test_index_realtime_comparison():
    """对比 akshare 和 xueqiu 的指数实时行情。"""
    print("\n" + "="*60)
    print("  INDEX REALTIME 对比测试 (akshare vs xueqiu)")
    print("="*60)

    from finance_data.provider.akshare.index.realtime import AkshareIndexQuote
    from finance_data.provider.xueqiu.index.realtime import XueqiuIndexQuote

    symbol = "000001.SH"  # 上证指数

    ak = AkshareIndexQuote()
    xq = XueqiuIndexQuote()

    ak_result, ak_err = run_test("akshare index realtime", ak.get_index_quote_realtime, symbol)
    xq_result, xq_err = run_test("xueqiu index realtime", xq.get_index_quote_realtime, symbol)

    if ak_err:
        print(f"  akshare ERROR: {ak_err}")
    if xq_err:
        print(f"  xueqiu ERROR: {xq_err}")

    if ak_result and ak_result.data:
        print(f"  akshare: {len(ak_result.data)} rows")
        print(f"    {ak_result.data[0]}")

    if xq_result and xq_result.data:
        print(f"  xueqiu: {len(xq_result.data)} rows")
        print(f"    {xq_result.data[0]}")

    results.append({
        "test": "index_realtime_comparison",
        "akshare": "PASS" if ak_result else "FAIL",
        "xueqiu": "PASS" if xq_result else "FAIL",
    })


def test_index_history_comparison():
    """对比 akshare 和 xueqiu 的指数历史K线。"""
    print("\n" + "="*60)
    print("  INDEX HISTORY 对比测试 (akshare vs xueqiu)")
    print("="*60)

    from finance_data.provider.akshare.index.history import AkshareIndexHistory
    from finance_data.provider.xueqiu.index.history import XueqiuIndexHistory

    symbol = "000001.SH"
    start = "20250106"
    end = "20250110"

    ak = AkshareIndexHistory()
    xq = XueqiuIndexHistory()

    ak_result, ak_err = run_test("akshare index history", ak.get_index_history, symbol, start, end)
    xq_result, xq_err = run_test("xueqiu index history", xq.get_index_history, symbol, start, end)

    if ak_err:
        print(f"  akshare ERROR: {ak_err}")
    if xq_err:
        print(f"  xueqiu ERROR: {xq_err}")

    if ak_result and ak_result.data:
        print(f"  akshare: {len(ak_result.data)} rows")
        for bar in ak_result.data[:3]:
            print(f"    {bar['date']}: close={bar['close']}, volume={bar['volume']:,}, amount={bar['amount']:,.0f}")

    if xq_result and xq_result.data:
        print(f"  xueqiu: {len(xq_result.data)} rows")
        for bar in xq_result.data[:3]:
            print(f"    {bar['date']}: close={bar['close']}, volume={bar['volume']:,}, amount={bar['amount']:,.0f}")

    results.append({
        "test": "index_history_comparison",
        "akshare": "PASS" if ak_result else "FAIL",
        "xueqiu": "PASS" if xq_result else "FAIL",
    })


def test_single_provider_all_interfaces():
    """测试单个 provider 的所有接口 (akshare)。"""
    print("\n" + "="*60)
    print("  AKSHARE 全接口测试")
    print("="*60)

    test_cases = [
        ("stock_info", lambda: __import__('finance_data.provider.akshare.stock.history', fromlist=['AkshareStockHistory']).AkshareStockHistory().get_stock_info_history, "000001"),
        ("kline_daily", lambda: __import__('finance_data.provider.akshare.kline.history', fromlist=['AkshareKlineHistory']).AkshareKlineHistory().get_kline_history, "000001", "daily", "20250101", "20250110", "qfq"),
        ("realtime", lambda: __import__('finance_data.provider.akshare.realtime.realtime', fromlist=['AkshareRealtimeQuote']).AkshareRealtimeQuote().get_realtime_quote, "000001"),
        ("index_quote", lambda: __import__('finance_data.provider.akshare.index.realtime', fromlist=['AkshareIndexQuote']).AkshareIndexQuote().get_index_quote_realtime, "000001.SH"),
        ("index_history", lambda: __import__('finance_data.provider.akshare.index.history', fromlist=['AkshareIndexHistory']).AkshareIndexHistory().get_index_history, "000001.SH", "20250101", "20250110"),
        ("market_stats", lambda: __import__('finance_data.provider.akshare.market.realtime', fromlist=['AkshareMarketRealtime']).AkshareMarketRealtime().get_market_stats_realtime),
    ]

    # margin 需要特殊处理
    margin_cases = [
        ("margin", lambda: __import__('finance_data.provider.akshare.margin.history', fromlist=['AkshareMargin']).AkshareMargin().get_margin_history, "20260320"),
        ("margin_detail", lambda: __import__('finance_data.provider.akshare.margin.history', fromlist=['AkshareMarginDetail']).AkshareMarginDetail().get_margin_detail_history, "20260320"),
    ]
    test_cases.extend(margin_cases)

    for name, fn, *args in test_cases:
        result, err = run_test(name, fn, *args)
        if err:
            print(f"  {RED}FAIL{RESET} {name}: {err}")
        else:
            rows = len(result.data) if result and result.data else 0
            print(f"  {GREEN}PASS{RESET} {name}: {rows} rows")
            results.append({"test": f"akshare_{name}", "status": "PASS", "rows": rows})
            if rows > 0:
                print(f"       sample: {result.data[0]}")
        results.append({"test": f"akshare_{name}", "status": "FAIL" if err else "PASS", "rows": 0})


# ==================== 主程序 ====================

if __name__ == "__main__":
    print("跨 Provider 数据对比测试")
    print(f"交易日: 20260320")

    # 测试各 provider 之间的数据对比
    test_kline_comparison()
    test_realtime_comparison()
    test_index_realtime_comparison()
    test_index_history_comparison()

    # 测试 akshare 全接口
    test_single_provider_all_interfaces()

    # 汇总
    print("\n" + "="*60)
    print("  汇总")
    print("="*60)

    pass_count = sum(1 for r in results if r.get("status") == "PASS")
    fail_count = sum(1 for r in results if r.get("status") == "FAIL")

    print(f"  {GREEN}{pass_count} PASS{RESET} / {RED}{fail_count} FAIL{RESET}")
    print("\n失败项:")
    for r in results:
        if r.get("status") == "FAIL":
            print(f"    - {r.get('test')}")
