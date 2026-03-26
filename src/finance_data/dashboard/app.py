"""FastAPI dashboard application"""
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from finance_data.dashboard.health import run_probes
from finance_data.dashboard.metrics import MetricsStore
from finance_data.dashboard.models import (
    HealthResult,
    InvokeRequest,
    InvokeResponse,
    ProviderStatus,
    ToolInfo,
)
from finance_data.provider.metadata.registry import TOOL_REGISTRY

logger = logging.getLogger(__name__)

app = FastAPI(title="FinanceData Dashboard", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_metrics = MetricsStore()

# --- Static files for production ---
_STATIC_DIR = Path(__file__).parent / "static"


def _get_providers_for_tool_name(tool_name: str) -> list[str]:
    """Return actual provider names from _TOOL_PROVIDERS mapping"""
    from finance_data.dashboard.health import _TOOL_PROVIDERS
    return list(_TOOL_PROVIDERS.get(tool_name, {}).keys())


# ------------------------------------------------------------------
# Tool metadata
# ------------------------------------------------------------------

@app.get("/api/tools")
async def get_tools() -> list[ToolInfo]:
    results = []
    for name, meta in TOOL_REGISTRY.items():
        results.append(ToolInfo(
            name=name,
            description=meta.description,
            domain=meta.domain,
            source=meta.source.value,
            source_priority=meta.source_priority,
            providers=_get_providers_for_tool_name(name),
            return_fields=meta.return_fields,
        ))
    return results


# ------------------------------------------------------------------
# Provider status
# ------------------------------------------------------------------

@app.get("/api/providers")
async def get_providers() -> list[ProviderStatus]:
    try:
        from finance_data.provider.tushare.client import is_token_valid
        has_tushare = is_token_valid()
    except Exception:
        has_tushare = False
    tushare_token_set = bool(os.getenv("TUSHARE_TOKEN"))
    if has_tushare:
        tushare_reason = "token valid"
    elif tushare_token_set:
        tushare_reason = "token set but invalid"
    else:
        tushare_reason = "TUSHARE_TOKEN not set"

    try:
        from finance_data.provider.xueqiu.client import has_login_cookie
        has_xueqiu = has_login_cookie()
    except Exception:
        has_xueqiu = False

    return [
        ProviderStatus(name="akshare", available=True, reason="no token needed"),
        ProviderStatus(name="tushare", available=has_tushare, reason=tushare_reason),
        ProviderStatus(
            name="xueqiu",
            available=has_xueqiu,
            reason="login cookie found" if has_xueqiu else "no login cookie",
        ),
    ]


# ------------------------------------------------------------------
# Health probes (SSE)
# ------------------------------------------------------------------

def _sse_stream(tool_name: Optional[str] = None):
    for result in run_probes(tool_name=tool_name):
        # Only record metrics for probe results, not consistency checks
        if isinstance(result, HealthResult):
            _metrics.record(
                tool=result.tool,
                provider=result.provider,
                status=result.status,
                response_time_ms=result.response_time_ms,
                error=result.error,
                source="probe",
            )
        data = result.model_dump_json()
        yield f"data: {data}\n\n"
    yield "data: [DONE]\n\n"


@app.post("/api/health")
async def health_all():
    return StreamingResponse(
        _sse_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/health/{tool_name}")
async def health_tool(tool_name: str):
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"unknown tool: {tool_name}"}
    return StreamingResponse(
        _sse_stream(tool_name=tool_name),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ------------------------------------------------------------------
# Metrics
# ------------------------------------------------------------------

@app.get("/api/metrics/latest")
async def metrics_latest(
    tool: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
):
    records = _metrics.get_latest(tool=tool, provider=provider)
    return [r.model_dump() for r in records]


@app.get("/api/metrics/stats")
async def metrics_stats(
    tool: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    hours: int = Query(24),
):
    stats = _metrics.get_stats(tool=tool, provider=provider, hours=hours)
    return [s.model_dump() for s in stats]


@app.get("/api/metrics/{tool}/{provider}")
async def metrics_history(tool: str, provider: str, limit: int = Query(50)):
    records = _metrics.get_history(tool=tool, provider=provider, limit=limit)
    return [r.model_dump() for r in records]


# ------------------------------------------------------------------
# Tool invocation
# ------------------------------------------------------------------

# Maps tool_name -> (service_module, dispatcher_attr, method_name)
_INVOKE_MAP = {
    "tool_get_stock_info_history": ("finance_data.service.stock", "stock_history", "get_stock_info_history"),
    "tool_get_kline_history": ("finance_data.service.kline", "kline_history", "get_kline_history"),
    "tool_get_realtime_quote": ("finance_data.service.realtime", "realtime_quote", "get_realtime_quote"),
    "tool_get_index_quote_realtime": ("finance_data.service.index", "index_quote", "get_index_quote_realtime"),
    "tool_get_index_history": ("finance_data.service.index", "index_history", "get_index_history"),
    "tool_get_sector_rank_realtime": ("finance_data.service.sector", "sector_rank", "get_sector_rank_realtime"),
    "tool_get_chip_distribution_history": ("finance_data.service.chip", "chip_history", "get_chip_distribution_history"),
    "tool_get_financial_summary_history": ("finance_data.service.fundamental", "financial_summary", "get_financial_summary_history"),
    "tool_get_dividend_history": ("finance_data.service.fundamental", "dividend", "get_dividend_history"),
    "tool_get_earnings_forecast_history": ("finance_data.service.fundamental", "earnings_forecast", "get_earnings_forecast_history"),
    "tool_get_stock_capital_flow_realtime": ("finance_data.service.cashflow", "stock_capital_flow", "get_stock_capital_flow_realtime"),
    "tool_get_trade_calendar_history": ("finance_data.service.calendar", "trade_calendar", "get_trade_calendar_history"),
    "tool_get_lhb_detail": ("finance_data.service.lhb", "lhb_detail", "get_lhb_detail_history"),
    "tool_get_lhb_stock_stat": ("finance_data.service.lhb", "lhb_stock_stat", "get_lhb_stock_stat_history"),
    "tool_get_lhb_active_traders": ("finance_data.service.lhb", "lhb_active_traders", "get_lhb_active_traders_history"),
    "tool_get_lhb_trader_stat": ("finance_data.service.lhb", "lhb_trader_stat", "get_lhb_trader_stat_history"),
    "tool_get_lhb_stock_detail": ("finance_data.service.lhb", "lhb_stock_detail", "get_lhb_stock_detail_history"),
    "tool_get_zt_pool": ("finance_data.service.pool", "zt_pool", "get_zt_pool_history"),
    "tool_get_strong_stocks": ("finance_data.service.pool", "strong_stocks", "get_strong_stocks_history"),
    "tool_get_previous_zt": ("finance_data.service.pool", "previous_zt", "get_previous_zt_history"),
    "tool_get_zbgc_pool": ("finance_data.service.pool", "zbgc_pool", "get_zbgc_pool_history"),
    "tool_get_north_stock_hold": ("finance_data.service.north_flow", "north_stock_hold", "get_north_stock_hold_history"),
    "tool_get_margin": ("finance_data.service.margin", "margin", "get_margin_history"),
    "tool_get_margin_detail": ("finance_data.service.margin", "margin_detail", "get_margin_detail_history"),
    "tool_get_market_stats_realtime": ("finance_data.service.market", "market_realtime", "get_market_stats_realtime"),
    "tool_get_market_north_capital": ("finance_data.service.north_flow", "north_flow", "get_north_flow_history"),
    "tool_get_sector_capital_flow": ("finance_data.service.sector_fund_flow", "sector_capital_flow", "get_sector_capital_flow_history"),
}


@app.post("/api/tools/{tool_name}")
async def invoke_tool(tool_name: str, req: InvokeRequest) -> InvokeResponse:
    if tool_name not in _INVOKE_MAP:
        return InvokeResponse(
            tool=tool_name, provider="unknown", status="error",
            error=f"unknown tool: {tool_name}",
        )

    chosen_provider = req.provider
    try:
        start = time.monotonic()

        if chosen_provider:
            # Direct provider call — bypass dispatcher
            from finance_data.dashboard.health import (
                _import_class,
                get_providers_for_tool,
            )
            provider_entries = get_providers_for_tool(tool_name)
            class_path = None
            method_name = None
            for pname, cpath, mname in provider_entries:
                if pname == chosen_provider:
                    class_path = cpath
                    method_name = mname
                    break
            if not class_path:
                return InvokeResponse(
                    tool=tool_name, provider=chosen_provider, status="error",
                    error=f"provider '{chosen_provider}' not available for {tool_name}",
                )
            cls = _import_class(class_path)
            instance = cls()
            method = getattr(instance, method_name)
            result = method(**req.params)
        else:
            # Dispatcher fallback chain
            import importlib
            module_path, dispatcher_attr, method_name = _INVOKE_MAP[tool_name]
            mod = importlib.import_module(module_path)
            dispatcher = getattr(mod, dispatcher_attr)
            method = getattr(dispatcher, method_name)
            result = method(**req.params)

        elapsed = round((time.monotonic() - start) * 1000, 1)
        actual_provider = chosen_provider or result.source
        _metrics.record(
            tool=tool_name,
            provider=actual_provider,
            status="ok",
            response_time_ms=elapsed,
            source="invoke",
        )
        return InvokeResponse(
            tool=tool_name,
            provider=actual_provider,
            status="ok",
            response_time_ms=elapsed,
            data={"data": result.data, "source": result.source, "meta": result.meta},
        )
    except Exception as e:
        _metrics.record(
            tool=tool_name,
            provider=chosen_provider or "unknown",
            status="error",
            response_time_ms=0,
            error=str(e)[:200],
            source="invoke",
        )
        return InvokeResponse(
            tool=tool_name,
            provider=chosen_provider or "unknown",
            status="error",
            error=str(e)[:200],
        )


# ------------------------------------------------------------------
# SPA fallback
# ------------------------------------------------------------------

@app.get("/{path:path}")
async def spa_fallback(path: str):
    from fastapi.responses import FileResponse

    if _STATIC_DIR.is_dir():
        # Serve static assets (JS, CSS, fonts, images) directly
        static_file = _STATIC_DIR / path
        if static_file.is_file() and _STATIC_DIR in static_file.resolve().parents:
            return FileResponse(str(static_file))
        # SPA fallback — all other routes get index.html
        index_file = _STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
    return {"message": "FinanceData Dashboard API", "docs": "/docs"}
