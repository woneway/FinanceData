"""FastAPI dashboard application"""
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from finance_data.dashboard.health import run_probes
from finance_data.dashboard.metrics import MetricsStore
from finance_data.dashboard.models import ConsistencyResult
from finance_data.dashboard.models import (
    HealthResult,
    InvokeRequest,
    InvokeResponse,
    ProviderStatus,
    ToolInfo,
)
from finance_data.tool_specs import (
    get_tool_spec,
    invoke_tool_spec,
    list_tool_specs,
)
from finance_data.tool_specs.invoke import ToolInvokeError

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


# ------------------------------------------------------------------
# Tool metadata
# ------------------------------------------------------------------

@app.get("/api/tools")
async def get_tools() -> list[ToolInfo]:
    results = []
    for spec in list_tool_specs():
        meta = spec.metadata
        results.append(ToolInfo(
            name=spec.name,
            description=spec.description,
            domain=spec.domain,
            display_name=spec.display_name,
            source=meta.source,
            source_priority=meta.source_priority,
            freshness=meta.data_freshness,
            supports_history=meta.supports_history,
            providers=[provider.name for provider in spec.providers],
            return_fields=list(spec.return_fields),
            params=[param.to_api_dict() for param in spec.params],
            examples=list(meta.examples),
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
    from finance_data.config import has_tushare_token
    tushare_token_set = has_tushare_token()
    if has_tushare:
        tushare_reason = "token valid"
    elif tushare_token_set:
        tushare_reason = "token set but invalid"
    else:
        tushare_reason = "config.toml tushare.token not set"

    try:
        from finance_data.provider.xueqiu.client import has_login_cookie
        has_xueqiu = has_login_cookie()
    except Exception:
        has_xueqiu = False

    return [
        ProviderStatus(name="akshare", available=True, reason="no token needed"),
        ProviderStatus(name="tencent", available=True, reason="qt.gtimg.cn, no token needed"),
        ProviderStatus(name="baostock", available=True, reason="no token needed, stable"),
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
        if isinstance(result, HealthResult):
            _metrics.record(
                tool=result.tool,
                provider=result.provider,
                status=result.status,
                response_time_ms=result.response_time_ms,
                error=result.error,
                source="probe",
            )
        elif isinstance(result, ConsistencyResult):
            _metrics.record_consistency(result)
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
    if get_tool_spec(tool_name) is None:
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


@app.get("/api/consistency/latest")
async def consistency_latest():
    results = _metrics.get_latest_consistency()
    return [r.model_dump() for r in results]


# ------------------------------------------------------------------
# Tool invocation
# ------------------------------------------------------------------

@app.post("/api/tools/{tool_name}")
async def invoke_tool(tool_name: str, req: InvokeRequest) -> InvokeResponse:
    spec = get_tool_spec(tool_name)
    if spec is None:
        return InvokeResponse(
            tool=tool_name, provider="unknown", status="error",
            error=f"unknown tool: {tool_name}",
        )

    chosen_provider = req.provider
    try:
        invoked = invoke_tool_spec(tool_name, req.params, provider=chosen_provider)
        result = invoked.result
        actual_provider = invoked.provider
        _metrics.record(
            tool=tool_name,
            provider=actual_provider,
            status="ok",
            response_time_ms=invoked.response_time_ms,
            source="invoke",
        )
        return InvokeResponse(
            tool=tool_name,
            provider=actual_provider,
            status="ok",
            response_time_ms=invoked.response_time_ms,
            data={"data": result.data, "source": result.source, "meta": result.meta},
        )
    except (ToolInvokeError, Exception) as e:
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
