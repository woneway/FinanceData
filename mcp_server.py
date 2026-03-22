"""MCP 启动入口"""
from finance_data.mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
