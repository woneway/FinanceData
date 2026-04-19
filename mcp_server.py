"""
FinanceData MCP 启动入口

使用方式：
  python mcp_server.py

配置从项目根目录 config.toml 读取，MCP 无需注入环境变量：
  {
    "mcpServers": {
      "finance-data": {
        "command": "python3",
        "args": ["/path/to/FinanceData/mcp_server.py"]
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
