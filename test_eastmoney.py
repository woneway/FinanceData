"""测试 eastmoney 连通性（关闭代理后运行）

使用方法：
    # 先关闭 ClashX 系统代理，然后运行：
    .venv/bin/python test_eastmoney.py
"""

import os
import time

# 清除所有代理环境变量
for k in ["http_proxy", "https_proxy", "all_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"]:
    os.environ.pop(k, None)

import akshare as ak


def test(name, func):
    t0 = time.time()
    try:
        df = func()
        elapsed = time.time() - t0
        print(f"  ✅ {name}: 成功 | {elapsed:.2f}s | {len(df)} 条")
        print(f"     {df.head(2).to_string()}\n")
    except Exception as e:
        elapsed = time.time() - t0
        err = str(e).split("(Caused by")[0].strip()
        print(f"  ❌ {name}: 失败 | {elapsed:.2f}s | {err}\n")


print("=" * 60)
print("eastmoney push2 API 连通性测试")
print("=" * 60)

# 代理状态检查
proxy = os.environ.get("http_proxy") or os.environ.get("https_proxy")
print(f"\n代理状态: {'⚠️  有代理 ' + proxy if proxy else '✅ 无代理'}\n")

print("--- push2 系列（eastmoney 行情 API）---")
test("日K线 push2his", lambda: ak.stock_zh_a_hist(
    symbol="000001", period="daily",
    start_date="20250320", end_date="20250325", adjust="qfq"))

test("实时行情 push2", lambda: ak.stock_zh_a_spot_em())

test("行业板块 push2", lambda: ak.stock_board_industry_name_em())

print("--- 非 push2（eastmoney 网页 API）---")
test("个股信息 www", lambda: ak.stock_individual_info_em(symbol="000001"))

print("--- 其他数据源 ---")
test("腾讯源K线", lambda: ak.stock_zh_a_daily(
    symbol="sz000001", start_date="20250320", end_date="20250325", adjust="qfq"))

print("=" * 60)
print("如果 push2 系列全部失败，说明你的网络无法直连 eastmoney 行情 API")
print("如果 push2 系列成功，说明关代理后可正常使用")
print("=" * 60)
