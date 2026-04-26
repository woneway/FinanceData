"""MCP 应用单例与共享 helper。

供 mcp/server.py 与 mcp/tools/<domain>.py 共享的 FastMCP 实例与 JSON 序列化 helper。
不暴露给项目外部消费方；外部 import 入口仍为 `from finance_data.mcp.server import mcp`。
"""
import json
import logging

from fastmcp import FastMCP

from finance_data.tool_specs.invoke import invoke_tool_spec

logger = logging.getLogger(__name__)
mcp = FastMCP("finance-data")


def _to_json(result) -> str:
    return json.dumps(
        {"data": result.data, "source": result.source, "meta": result.meta},
        ensure_ascii=False,
        indent=2,
    )


def _invoke_tool_json(tool: str, params: dict) -> str:
    try:
        return _to_json(invoke_tool_spec(tool, params).result)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
