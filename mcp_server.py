"""
FinanceData MCP 启动入口

使用方式：
  python mcp_server.py

MCP 配置（Claude Desktop / claude.json）：
  {
    "mcpServers": {
      "finance-data": {
        "command": "python3",
        "args": ["/path/to/FinanceData/mcp_server.py"],
        "env": {
          "TUSHARE_TOKEN": "your_token_here"
        }
      }
    }
  }
"""
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

from finance_data.mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
