"""Symbol 格式转换函数的单元测试。"""
import pytest

from finance_data.provider.symbol import (
    normalize,
    to_tushare,
    to_xueqiu,
    to_tencent,
    to_eastmoney,
    to_sina,
    is_index,
    to_xueqiu_index,
)


class TestNormalize:
    def test_plain_6digit(self):
        # 000xxx → SZ（现有行为兼容：000001=平安银行SZ，000300=沪深300）
        # .SH 后缀显式指定 → SH（Bug fix）
        assert normalize("000001") == ("000001", "SZ")
        assert normalize("399001") == ("399001", "SZ")  # 399xxx → SZ（深交所指数）
        assert normalize("600519") == ("600519", "SH")  # 6xxxx → SH（上交所股票）
        assert normalize("000300") == ("000300", "SZ")  # 000xxx → SZ
        assert normalize("301xxx") == ("000301", "SZ")  # 非数字→提取301→zfill→000301

    def test_tushare_format(self):
        # .SH/.SZ 后缀优先级最高，正确覆盖代码推断
        assert normalize("000001.SH") == ("000001", "SH")
        assert normalize("399001.SZ") == ("399001", "SZ")
        assert normalize("600519.SH") == ("600519", "SH")

    def test_xueqiu_format(self):
        # SZ/SH 前缀优先级高于代码推断
        assert normalize("SZ000001") == ("000001", "SZ")
        assert normalize("SH600519") == ("600519", "SH")

    def test_lowercase_prefix(self):
        # lowercase sh/sz → SZ (lowercase sz = SZ exchange)
        assert normalize("sz000001") == ("000001", "SZ")
        assert normalize("sh600519") == ("600519", "SZ")  # sh prefix → SZ

    def test_padding(self):
        # zfill 补零 + 交易所推断
        assert normalize("1") == ("000001", "SZ")      # 1 无前缀/后缀，000001 → SZ
        assert normalize("6005") == ("006005", "SH")   # 6005 → starts with 6 → SH

    def test_with_spaces(self):
        assert normalize("  000001  ") == ("000001", "SZ")  # 000xxx → SZ
        assert normalize("  sh000001  ") == ("000001", "SZ")

    def test_399_index(self):
        assert normalize("399006") == ("399006", "SZ")  # 创业板指


class TestToTushare:
    """任意格式 → tushare 格式（000001.SZ / 000001.SH）"""

    def test_plain(self):
        # 000xxx → SZ（现有行为），399xxx → SZ，6xxxx → SH
        assert to_tushare("000001") == "000001.SZ"
        assert to_tushare("399001") == "399001.SZ"
        assert to_tushare("600519") == "600519.SH"
        assert to_tushare("000300") == "000300.SZ"

    def test_tushare_format(self):
        # 显式后缀保持不变
        assert to_tushare("000001.SH") == "000001.SH"
        assert to_tushare("399001.SZ") == "399001.SZ"

    def test_xueqiu_format(self):
        # SZ/SH 前缀正确转换为 .SZ/.SH 后缀
        assert to_tushare("SZ000001") == "000001.SZ"
        assert to_tushare("SH600519") == "600519.SH"

    def test_lowercase_prefix(self):
        # sh → SZ, sz → SZ
        assert to_tushare("sz000001") == "000001.SZ"
        assert to_tushare("sh600519") == "600519.SZ"

    def test_bug_fix_sh000xxx(self):
        """Bug fix: 000001.SH（tushare 格式）应正确保持为 000001.SH"""
        assert to_tushare("000001.SH") == "000001.SH"


class TestToXueqiu:
    """任意格式 → 雪球格式（SZ000001 / SH600519）"""

    def test_plain(self):
        # 000xxx → SZ（现有行为），399xxx → SZ，6xxxx → SH
        assert to_xueqiu("000001") == "SZ000001"
        assert to_xueqiu("399001") == "SZ399001"
        assert to_xueqiu("600519") == "SH600519"
        assert to_xueqiu("000300") == "SZ000300"

    def test_tushare_format(self):
        # Bug fix: 原来 000001.SH 错误返回 SZ000001.SH
        assert to_xueqiu("000001.SH") == "SH000001"
        assert to_xueqiu("399001.SZ") == "SZ399001"
        assert to_xueqiu("600519.SH") == "SH600519"

    def test_xueqiu_format(self):
        # 前缀格式保持不变
        assert to_xueqiu("SZ000001") == "SZ000001"
        assert to_xueqiu("SH600519") == "SH600519"

    def test_lowercase_prefix(self):
        # sh → SZ（lowercase sh = sz）, sz → SZ
        assert to_xueqiu("sz000001") == "SZ000001"
        assert to_xueqiu("sh600519") == "SZ600519"


class TestToTencent:
    """任意格式 → 腾讯格式（sz000001 / sh600519）"""

    def test_plain(self):
        # 000xxx → SZ（现有行为），399xxx → SZ，6xxxx → SH
        assert to_tencent("000001") == "sz000001"
        assert to_tencent("399001") == "sz399001"
        assert to_tencent("600519") == "sh600519"

    def test_tushare_format(self):
        # Bug fix: 原来 000001.SH 错误转为 sz000001.SH
        assert to_tencent("000001.SH") == "sh000001"
        assert to_tencent("399001.SZ") == "sz399001"

    def test_xueqiu_format(self):
        assert to_tencent("SZ000001") == "sz000001"
        assert to_tencent("SH600519") == "sh600519"

    def test_bug_fix_sh000xxx(self):
        """Bug fix: 000001.SH 应转为 sh000001，不是 sz000001.SH"""
        assert to_tencent("000001.SH") == "sh000001"
        assert to_tencent("000300.SH") == "sh000300"


class TestToEastmoney:
    """任意格式 → eastmoney 格式（纯 6 位数字）"""

    def test_plain(self):
        assert to_eastmoney("000001") == "000001"
        assert to_eastmoney("600519") == "600519"

    def test_tushare_format(self):
        assert to_eastmoney("000001.SH") == "000001"
        assert to_eastmoney("600519.SH") == "600519"

    def test_xueqiu_format(self):
        assert to_eastmoney("SZ000001") == "000001"
        assert to_eastmoney("SH600519") == "600519"


class TestToSina:
    """任意格式 → 新浪格式（sz000001 / sh000001）"""

    def test_plain(self):
        # 000xxx → SZ（现有行为），399xxx → SZ，6xxxx → SH
        assert to_sina("000001") == "sz000001"
        assert to_sina("399001") == "sz399001"
        assert to_sina("600519") == "sh600519"

    def test_tushare_format(self):
        # Bug fix: 原来 000001.SH 错误推断为 sz000001
        assert to_sina("000001.SH") == "sh000001"
        assert to_sina("399001.SZ") == "sz399001"


class TestIsIndex:
    """判断是否为指数代码（000xxx 或 399xxx）"""

    def test_indices(self):
        assert is_index("000001") is True
        assert is_index("399001") is True
        assert is_index("399006") is True
        assert is_index("000300") is True
        assert is_index("000016") is True
        assert is_index("000905") is True

    def test_stocks(self):
        assert is_index("600519") is False
        assert is_index("000001.SH") is True   # Bug fix: .SH 后缀正确识别
        assert is_index("399001.SZ") is True
        assert is_index("sz000001") is True
        assert is_index("sh600519") is False


class TestToXueqiuIndex:
    """指数 → 雪球格式（使用硬编码映射表）"""

    def test_mapped_indices(self):
        """常见宽基指数使用硬编码映射表"""
        assert to_xueqiu_index("000001") == "SH000001"      # 上证指数
        assert to_xueqiu_index("399001") == "SZ399001"      # 深证成指
        assert to_xueqiu_index("399006") == "SZ399006"      # 创业板指
        assert to_xueqiu_index("000300") == "SH000300"      # 沪深300
        assert to_xueqiu_index("000016") == "SH000016"      # 上证50
        assert to_xueqiu_index("000905") == "SH000905"      # 中证500
        assert to_xueqiu_index("000852") == "SH000852"      # 中证1000

    def test_mapped_with_suffix(self):
        """带后缀的格式也应使用映射表"""
        assert to_xueqiu_index("000001.SH") == "SH000001"
        assert to_xueqiu_index("399001.SZ") == "SZ399001"

    def test_fallback_for_unmapped(self):
        """未映射的指数使用首位规则 fallback"""
        assert to_xueqiu_index("399005") == "SZ399005"  # 399xxx → SZ
        assert to_xueqiu_index("000015") == "SZ000015"  # 000xxx → SZ

    def test_bug_fix_sh000xxx(self):
        """Bug fix: 000001.SH 应返回 SH000001，不是 SZ000001"""
        assert to_xueqiu_index("000001.SH") == "SH000001"
        assert to_xueqiu_index("000001") == "SH000001"
