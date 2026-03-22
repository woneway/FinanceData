# FinanceData

金融数据服务，支持 MCP（AI Agent）和 Python library 两种接入方式。

## MCP 配置

```json
{
  "mcpServers": {
    "finance-data": {
      "command": "/Users/lianwu/ai/projects/FinanceData/.venv/bin/python",
      "args": ["/Users/lianwu/ai/projects/FinanceData/mcp_server.py"],
      "env": {
        "TUSHARE_TOKEN": "your_token"
      }
    }
  }
}
```

## 环境变量

- `TUSHARE_TOKEN`：tushare API token（tushare 接口必须）

## 开发

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -v
```

## 新增接口流程

1. 在 `src/finance_data/provider/akshare/` 或 `tushare/` 下添加函数
2. 在 `tests/provider/` 下添加对应测试
3. 在 `src/finance_data/mcp/server.py` 添加 MCP tool
4. 更新 CLAUDE.md 接口列表

## 当前接口

| Tool | 数据源 | 说明 |
|------|--------|------|
| `get_stock_info` | akshare | 个股基本信息 |
