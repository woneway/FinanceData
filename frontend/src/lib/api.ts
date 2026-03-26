// --- Types matching backend Pydantic models ---

export interface CallRecord {
  tool: string
  provider: string
  timestamp: string
  status: "ok" | "error" | "timeout"
  response_time_ms: number
  error: string | null
  source: "probe" | "invoke"
}

export interface ToolStats {
  tool: string
  provider: string
  total_calls: number
  success_count: number
  success_rate: number
  avg_response_ms: number
  last_status: string | null
  last_check_time: string | null
  last_error: string | null
}

export interface ToolInfo {
  name: string
  description: string
  domain: string
  source: string
  source_priority: string
  providers: string[]
  return_fields: string[]
}

export interface ProviderStatus {
  name: string
  available: boolean
  reason: string
}

export interface HealthResult {
  tool: string
  provider: string
  status: "ok" | "error" | "timeout"
  response_time_ms: number
  error: string | null
  record_count: number
}

export interface InvokeResponse {
  tool: string
  provider: string
  status: "ok" | "error"
  response_time_ms: number
  data: unknown
  error: string | null
}

// --- API functions ---

export async function fetchTools(): Promise<ToolInfo[]> {
  const res = await fetch("/api/tools")
  if (!res.ok) throw new Error(`Failed to fetch tools: ${res.status}`)
  return res.json()
}

export async function fetchProviders(): Promise<ProviderStatus[]> {
  const res = await fetch("/api/providers")
  if (!res.ok) throw new Error(`Failed to fetch providers: ${res.status}`)
  return res.json()
}

export async function fetchLatestMetrics(
  tool?: string,
  provider?: string,
): Promise<CallRecord[]> {
  const params = new URLSearchParams()
  if (tool) params.set("tool", tool)
  if (provider) params.set("provider", provider)
  const qs = params.toString()
  const res = await fetch(`/api/metrics/latest${qs ? `?${qs}` : ""}`)
  if (!res.ok) throw new Error(`Failed to fetch latest metrics: ${res.status}`)
  return res.json()
}

export async function fetchStats(hours = 24): Promise<ToolStats[]> {
  const res = await fetch(`/api/metrics/stats?hours=${hours}`)
  if (!res.ok) throw new Error(`Failed to fetch stats: ${res.status}`)
  return res.json()
}

export async function fetchHistory(
  tool: string,
  provider: string,
  limit = 50,
): Promise<CallRecord[]> {
  const res = await fetch(`/api/metrics/${tool}/${provider}?limit=${limit}`)
  if (!res.ok) throw new Error(`Failed to fetch history: ${res.status}`)
  return res.json()
}

export async function invokeTool(
  tool: string,
  params: Record<string, unknown>,
): Promise<InvokeResponse> {
  const res = await fetch(`/api/tools/${tool}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ params }),
  })
  if (!res.ok) throw new Error(`Failed to invoke tool: ${res.status}`)
  return res.json()
}

// --- SSE helper ---

export async function runHealthCheck(
  onResult: (result: HealthResult) => void,
  onDone: () => void,
  toolName?: string,
): Promise<void> {
  const url = toolName ? `/api/health/${toolName}` : "/api/health"
  const res = await fetch(url, { method: "POST" })
  if (!res.ok || !res.body) {
    throw new Error(`Health check failed: ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const lines = buffer.split("\n")
    buffer = lines.pop() ?? ""

    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed.startsWith("data: ")) continue
      const payload = trimmed.slice(6)
      if (payload === "[DONE]") {
        onDone()
        return
      }
      try {
        const result: HealthResult = JSON.parse(payload)
        onResult(result)
      } catch {
        // skip malformed lines
      }
    }
  }
  onDone()
}
