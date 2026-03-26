"""FinanceData Dashboard entry point"""
import uvicorn

from finance_data.dashboard.app import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8100)
