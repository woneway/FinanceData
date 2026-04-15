"""接口元数据校验器"""
import re
import inspect
from typing import Dict, List, Any
from finance_data.provider.metadata.registry import TOOL_REGISTRY
from finance_data.tool_specs import get_tool_service_target, get_tool_spec, list_tool_specs


class ValidationResult:
    def __init__(self, passed: bool, message: str, tool_name: str = ""):
        self.passed = passed
        self.message = message
        self.tool_name = tool_name

    def __str__(self) -> str:
        status = "[PASS]" if self.passed else "[FAIL]"
        return f"{status} {self.tool_name} - {self.message}"


class Validator:
    """
    FinanceData 接口校验器

    校验维度：
    1. docstring 完整性
    2. docstring 格式规范
    3. docstring 包含必要章节
    4. 与 ToolMeta 元数据一致性
    5. 参数命名规范
    6. 与 ToolSpec 签名 / service target 一致
    """

    REQUIRED_SECTIONS = [
        "数据源",
        "实时性",
        "历史查询",
        "Args:",
        "Returns:",
    ]

    PARAM_PATTERNS = {
        r"trade_date|单日查询|交易日期": "trade_date",
        r"start_date.*end_date|日期范围": "start_date + end_date",
        r"symbol|股票代码": "symbol",
        r"period|K线周期": "period",
    }

    def __init__(self, server_module):
        self.server_module = server_module
        self.tool_functions = self._extract_tool_functions()

    def _extract_tool_functions(self) -> Dict[str, Any]:
        """从 server.py 提取所有 @mcp.tool() 装饰的函数"""
        tools = {}
        for name in dir(self.server_module):
            if name.startswith("tool_"):
                fn = getattr(self.server_module, name)
                if callable(fn):
                    tools[name] = fn
        return tools

    def validate_all(self) -> List[ValidationResult]:
        """执行所有校验"""
        results = []

        # 1. 校验 ToolMeta 完整性
        results.extend(self._validate_meta_completeness())

        # 2. 校验 docstring 完整性
        results.extend(self._validate_docstrings())

        # 3. 校验 docstring 格式
        results.extend(self._validate_docstring_format())

        # 4. 校验参数命名
        results.extend(self._validate_param_naming())

        # 5. 校验数量一致性
        results.extend(self._validate_tool_count())

        # 6. 校验 ToolSpec 对齐
        results.extend(self._validate_toolspec_signature_alignment())
        results.extend(self._validate_toolspec_dispatch_alignment())

        return results

    def _validate_meta_completeness(self) -> List[ValidationResult]:
        """校验 ToolMeta 完整性"""
        results = []
        for name, meta in TOOL_REGISTRY.items():
            if not meta.description:
                results.append(ValidationResult(False, "ToolMeta.description 为空", name))
            if not meta.api_name:
                results.append(ValidationResult(False, "ToolMeta.api_name 为空", name))
            if not meta.return_fields:
                results.append(ValidationResult(False, "ToolMeta.return_fields 为空", name))
        return results

    def _validate_docstrings(self) -> List[ValidationResult]:
        """校验 docstring 包含必要章节"""
        results = []

        for name, fn in self.tool_functions.items():
            doc = fn.__doc__ or ""

            for section in self.REQUIRED_SECTIONS:
                if section not in doc:
                    results.append(ValidationResult(
                        False,
                        f"docstring 缺少章节: '{section}'",
                        name
                    ))

            # 额外检查：必须有详细参数说明
            if "Args:" not in doc and "参数" not in doc:
                results.append(ValidationResult(
                    False,
                    "docstring 缺少 Args/参数说明",
                    name
                ))

        return results

    def _validate_docstring_format(self) -> List[ValidationResult]:
        """校验 docstring 格式规范"""
        results = []

        for name, fn in self.tool_functions.items():
            doc = fn.__doc__ or ""

            # 检查实时性描述
            if "实时" in doc and "非实时" not in doc and "收盘后" not in doc:
                # 可能是 realtime，但没有说明
                pass  # 暂不强制

            # 检查是否有 UpdateTiming 相关描述
            has_timing = any(x in doc for x in ["T+0", "T+1", "15:30", "16:00", "17:00"])
            if not has_timing and "实时" in doc:
                results.append(ValidationResult(
                    False,
                    "docstring 未说明更新时机（如 T+1_15:30）",
                    name
                ))

        return results

    def _validate_param_naming(self) -> List[ValidationResult]:
        """校验参数命名规范"""
        results = []

        for name, fn in self.tool_functions.items():
            sig = inspect.signature(fn)
            param_names = list(sig.parameters.keys())

            # 检查是否有 start_date/end_date
            has_range = "start_date" in param_names and "end_date" in param_names

            # 获取 docstring
            doc = fn.__doc__ or ""

            # 如果描述中提到"日期范围"，但没有 start_date/end_date 参数
            if "日期范围" in doc and not has_range:
                results.append(ValidationResult(
                    False,
                    "描述中提到'日期范围'但缺少 start_date/end_date 参数",
                    name
                ))

        return results

    def _validate_tool_count(self) -> List[ValidationResult]:
        """校验 ToolMeta 数量与实际接口一致"""
        results = []

        # 从函数名提取 tool 数量
        tool_count = len(self.tool_functions)
        meta_count = len(TOOL_REGISTRY)

        if tool_count != meta_count:
            results.append(ValidationResult(
                False,
                f"ToolMeta 数量({meta_count}) 与实际工具({tool_count})不一致",
                "registry"
            ))

        # 检查是否有遗漏
        for name in self.tool_functions:
            if name not in TOOL_REGISTRY:
                results.append(ValidationResult(
                    False,
                    f"工具 '{name}' 未在 TOOL_REGISTRY 中注册",
                    name
                ))

        return results

    def _validate_toolspec_signature_alignment(self) -> List[ValidationResult]:
        """校验 MCP 函数签名与 ToolSpec 参数定义一致。"""
        results = []

        for name, fn in self.tool_functions.items():
            spec = get_tool_spec(name)
            if spec is None:
                results.append(ValidationResult(False, "ToolSpec 未注册", name))
                continue

            sig = inspect.signature(fn)
            actual_params = []
            for param in sig.parameters.values():
                if param.name in {"self", "cls"}:
                    continue
                actual_params.append(
                    (
                        param.name,
                        param.default is inspect._empty,
                        None if param.default is inspect._empty else param.default,
                    )
                )

            expected_params = [
                (param.name, param.required, param.default)
                for param in spec.params
            ]

            if actual_params != expected_params:
                results.append(ValidationResult(
                    False,
                    f"ToolSpec 参数与 MCP 签名不一致: expected={expected_params}, actual={actual_params}",
                    name,
                ))

        return results

    def _validate_toolspec_dispatch_alignment(self) -> List[ValidationResult]:
        """校验 MCP 函数实现通过 ToolSpec dispatch 进入 service target。"""
        results = []

        for name, fn in self.tool_functions.items():
            target = get_tool_service_target(name)
            if target is None:
                results.append(ValidationResult(False, "ToolSpec service target 缺失", name))
                continue

            try:
                source = inspect.getsource(fn)
            except OSError as exc:
                results.append(ValidationResult(
                    False,
                    f"MCP 源码不可读，无法校验 ToolSpec dispatch: {exc}",
                    name,
                ))
                continue

            if "_invoke_tool_json" not in source or name not in source:
                results.append(ValidationResult(
                    False,
                    f"MCP 未通过 ToolSpec dispatch 调用注册工具: {name}",
                    name,
                ))

        return results

    def run_report(self) -> str:
        """生成校验报告"""
        results = self.validate_all()
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)

        lines = [
            "=" * 60,
            "FinanceData 接口校验报告",
            "=" * 60,
            f"总计: {passed + failed} 项",
            f"通过: {passed}",
            f"失败: {failed}",
            "-" * 60,
        ]

        if failed > 0:
            lines.append("失败项:")
            for r in results:
                if not r.passed:
                    lines.append(f"  {r}")

        lines.append("=" * 60)

        return "\n".join(lines)


def validate_all_tools() -> List[ValidationResult]:
    """便捷函数：校验所有工具"""
    # 动态导入 server 模块
    import importlib
    server = importlib.import_module("finance_data.mcp.server")
    validator = Validator(server)
    return validator.validate_all()


def validate_toolspec_registry_consistency() -> List[ValidationResult]:
    """校验 ToolSpec / ToolMeta / MCP 显式函数三者一致。"""
    import importlib

    results: List[ValidationResult] = []
    server = importlib.import_module("finance_data.mcp.server")
    validator = Validator(server)

    meta_names = set(TOOL_REGISTRY.keys())
    spec_names = {spec.name for spec in list_tool_specs()}
    tool_names = set(validator.tool_functions.keys())

    if meta_names != spec_names:
        results.append(ValidationResult(
            False,
            f"ToolMeta 与 ToolSpec 注册集合不一致: meta_only={sorted(meta_names - spec_names)}, spec_only={sorted(spec_names - meta_names)}",
            "registry",
        ))

    if tool_names != spec_names:
        results.append(ValidationResult(
            False,
            f"MCP tools 与 ToolSpec 注册集合不一致: mcp_only={sorted(tool_names - spec_names)}, spec_only={sorted(spec_names - tool_names)}",
            "registry",
        ))

    results.extend(validator._validate_toolspec_signature_alignment())
    results.extend(validator._validate_toolspec_dispatch_alignment())
    return results


def run_validation_report() -> str:
    """运行校验并生成报告"""
    import importlib
    server = importlib.import_module("finance_data.mcp.server")
    validator = Validator(server)
    return validator.run_report()


if __name__ == "__main__":
    print(run_validation_report())
