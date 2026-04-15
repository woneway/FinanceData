import { useCallback, useEffect, useMemo, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  type ConsistencyResult,
  type HealthResult,
  type ToolInfo,
  type ToolStats,
  fetchConsistencyLatest,
  fetchStats,
  runHealthCheck,
} from "@/lib/api"

type StatusFilter = "all" | "ok" | "error"
type TimeRange = "1" | "6" | "24" | "168"

const DOMAIN_LABELS: Record<string, string> = {
  stock: "个股信息",
  kline: "K线数据",
  quote: "实时行情",
  index: "指数数据",
  board: "板块数据",
  chip: "筹码分布",
  fundamental: "基本面",
  cashflow: "资金流向",
  calendar: "交易日历",
  lhb: "龙虎榜",
  pool: "题材股池",
  north_flow: "北向资金",
  margin: "融资融券",
  market: "大盘统计",
  sector_fund_flow: "板块资金流",
  daily_basic: "日频指标",
  limit_price: "涨跌停价",
  suspend: "停复牌",
  hot_rank: "人气排行",
}

interface HealthCheckProps {
  tools: ToolInfo[]
}

/** Per-provider aggregate stats */
interface ProviderSummary {
  name: string
  toolCount: number
  okCount: number
  errorCount: number
  unknownCount: number
  avgMs: number
  totalCalls: number
  successRate: string
}

export default function HealthCheck({ tools }: HealthCheckProps) {
  const [stats, setStats] = useState<ToolStats[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [total, setTotal] = useState(0)
  const [liveResults, setLiveResults] = useState<Map<string, HealthResult>>(
    new Map(),
  )
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all")
  const [timeRange, setTimeRange] = useState<TimeRange>("24")
  const [probingTool, setProbingTool] = useState<string | null>(null)
  const [consistencyResults, setConsistencyResults] = useState<Map<string, ConsistencyResult>>(
    new Map(),
  )

  const loadStats = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchStats(Number(timeRange))
      setStats(data)
    } catch (e) {
      console.error("Failed to load stats:", e)
    } finally {
      setLoading(false)
    }
  }, [timeRange])

  const loadConsistency = useCallback(async () => {
    try {
      const data = await fetchConsistencyLatest()
      if (data.length > 0) {
        setConsistencyResults(new Map(data.map((c) => [c.tool, c])))
      }
    } catch (e) {
      console.error("Failed to load consistency:", e)
    }
  }, [])

  useEffect(() => {
    loadStats()
    loadConsistency()
  }, [loadStats, loadConsistency])

  useEffect(() => {
    const count = tools.reduce((sum, t) => sum + t.providers.length, 0)
    setTotal(count)
  }, [tools])

  const onConsistencyResult = useCallback((cr: ConsistencyResult) => {
    setConsistencyResults((prev) => {
      const next = new Map(prev)
      next.set(cr.tool, cr)
      return next
    })
  }, [])

  const handleRunAll = async () => {
    setRunning(true)
    setLiveResults(new Map())
    setConsistencyResults(new Map())
    setProgress(0)
    try {
      await runHealthCheck(
        (result) => {
          setLiveResults((prev) => {
            const next = new Map(prev)
            next.set(`${result.tool}:${result.provider}`, result)
            return next
          })
          setProgress((p) => p + 1)
        },
        () => {
          setRunning(false)
          loadStats()
        },
        undefined,
        onConsistencyResult,
      )
    } catch (e) {
      console.error("Health check failed:", e)
      setRunning(false)
    }
  }

  const handleProbeTool = async (toolName: string) => {
    if (running || probingTool) return
    setProbingTool(toolName)
    try {
      await runHealthCheck(
        (result) => {
          setLiveResults((prev) => {
            const next = new Map(prev)
            next.set(`${result.tool}:${result.provider}`, result)
            return next
          })
        },
        () => {
          setProbingTool(null)
          loadStats()
        },
        toolName,
        onConsistencyResult,
      )
    } catch (e) {
      console.error("Single probe failed:", e)
      setProbingTool(null)
    }
  }

  // All unique providers across all tools, sorted
  const allProviders = useMemo(() => {
    const set = new Set<string>()
    for (const t of tools) {
      for (const p of t.providers) set.add(p)
    }
    return Array.from(set).sort((a, b) => {
      const order = ["akshare", "tencent", "baostock", "tushare", "xueqiu"]
      return (order.indexOf(a) === -1 ? 99 : order.indexOf(a)) -
        (order.indexOf(b) === -1 ? 99 : order.indexOf(b))
    })
  }, [tools])

  // Stats lookup
  const statsLookup = useMemo(() => {
    const map = new Map<string, ToolStats>()
    for (const s of stats) {
      map.set(`${s.tool}:${s.provider}`, s)
    }
    return map
  }, [stats])

  // Get effective status for a tool:provider pair
  const getStatus = useCallback(
    (toolName: string, provider: string) => {
      const key = `${toolName}:${provider}`
      const live = liveResults.get(key)
      const stat = statsLookup.get(key)
      return {
        status: live?.status ?? stat?.last_status ?? null,
        timeMs: live?.response_time_ms ?? stat?.avg_response_ms ?? null,
        stat,
        live,
        isLive: !!live,
      }
    },
    [liveResults, statsLookup],
  )

  // Provider summaries
  const providerSummaries = useMemo<ProviderSummary[]>(() => {
    return allProviders.map((name) => {
      const providerTools = tools.filter((t) => t.providers.includes(name))
      let ok = 0, error = 0, unknown = 0, totalMs = 0, msCount = 0, totalCalls = 0, successCount = 0
      for (const t of providerTools) {
        const { status, timeMs, stat } = getStatus(t.name, name)
        if (status === "ok" || status === "warn") ok++
        else if (status === "error" || status === "timeout") error++
        else unknown++
        if (timeMs != null) { totalMs += timeMs; msCount++ }
        if (stat) { totalCalls += stat.total_calls; successCount += stat.success_count }
      }
      return {
        name,
        toolCount: providerTools.length,
        okCount: ok,
        errorCount: error,
        unknownCount: unknown,
        avgMs: msCount > 0 ? Math.round(totalMs / msCount) : 0,
        totalCalls,
        successRate: totalCalls > 0 ? ((successCount / totalCalls) * 100).toFixed(1) : "--",
      }
    })
  }, [allProviders, tools, getStatus])

  // Domain groups
  const domainGroups = useMemo(() => {
    const groups = new Map<string, ToolInfo[]>()
    for (const tool of tools) {
      const group = groups.get(tool.domain) ?? []
      group.push(tool)
      groups.set(tool.domain, group)
    }
    return groups
  }, [tools])

  // Filter
  const shouldShowTool = useCallback(
    (tool: ToolInfo) => {
      if (statusFilter === "all") return true
      for (const provider of tool.providers) {
        const { status } = getStatus(tool.name, provider)
        if (statusFilter === "ok" && status === "ok") return true
        if (statusFilter === "error" && status !== "ok" && status != null) return true
      }
      return false
    },
    [statusFilter, getStatus],
  )

  // Recent errors
  const recentErrors = useMemo(() => {
    const errors: { tool: string; provider: string; error: string; time: string | null }[] = []
    for (const [key, live] of liveResults) {
      if (live.status === "error" || live.status === "timeout") {
        const [tool, provider] = key.split(":")
        errors.push({ tool, provider, error: live.error ?? live.status, time: "刚刚" })
      }
    }
    for (const s of stats) {
      if (s.last_status === "error" || s.last_status === "timeout") {
        const key = `${s.tool}:${s.provider}`
        if (!liveResults.has(key) && s.last_error) {
          errors.push({
            tool: s.tool,
            provider: s.provider,
            error: s.last_error,
            time: s.last_check_time ? timeAgo(s.last_check_time) : null,
          })
        }
      }
    }
    return errors.slice(0, 10)
  }, [stats, liveResults])

  const hasAnyData = stats.length > 0 || liveResults.size > 0

  return (
    <div className="space-y-6">
      {/* Provider Overview - Compact */}
      <Card>
        <CardContent className="py-3">
          <div className="flex items-center gap-6 flex-wrap">
            {/* Total */}
            <div className="flex items-center gap-2 text-sm">
              <span className="font-semibold">{tools.length}</span>
              <span className="text-muted-foreground">接口</span>
              <span className="text-muted-foreground">·</span>
              <span className="font-semibold">{domainGroups.size}</span>
              <span className="text-muted-foreground">领域</span>
              <span className="text-muted-foreground">·</span>
              <span className="font-semibold">{allProviders.length}</span>
              <span className="text-muted-foreground">数据源</span>
              <span className="text-muted-foreground">·</span>
              <span className="font-semibold">{total}</span>
              <span className="text-muted-foreground">探测点</span>
            </div>
            <div className="h-4 w-px bg-border" />
            {/* Per-provider compact */}
            {providerSummaries.map((p) => (
              <div key={p.name} className="flex items-center gap-2 text-sm">
                <span className="font-medium min-w-[60px]">{p.name}</span>
                <span className="text-muted-foreground text-xs">{p.toolCount}个</span>
                <div className="flex items-center gap-1">
                  {p.okCount > 0 && (
                    <span className="flex items-center gap-0.5 text-green-600 text-xs">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                      {p.okCount}
                    </span>
                  )}
                  {p.errorCount > 0 && (
                    <span className="flex items-center gap-0.5 text-red-600 text-xs">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                      {p.errorCount}
                    </span>
                  )}
                  {p.unknownCount > 0 && (
                    <span className="flex items-center gap-0.5 text-gray-400 text-xs">
                      <span className="w-1.5 h-1.5 rounded-full bg-gray-300" />
                      {p.unknownCount}
                    </span>
                  )}
                </div>
                {p.avgMs > 0 && (
                  <span className="font-mono text-xs text-muted-foreground">{p.avgMs}ms</span>
                )}
                {p.successRate !== "--" && (
                  <span className={`text-xs font-medium ${
                    Number(p.successRate) >= 95 ? "text-green-600"
                      : Number(p.successRate) >= 80 ? "text-yellow-600"
                      : "text-red-600"
                  }`}>
                    {p.successRate}%
                  </span>
                )}
                {/* Mini bar */}
                {(p.okCount > 0 || p.errorCount > 0) && (
                  <div className="flex h-1 w-12 rounded-full overflow-hidden bg-muted">
                    {p.okCount > 0 && (
                      <div className="bg-green-500" style={{ width: `${(p.okCount / p.toolCount) * 100}%` }} />
                    )}
                    {p.errorCount > 0 && (
                      <div className="bg-red-500" style={{ width: `${(p.errorCount / p.toolCount) * 100}%` }} />
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Consistency Summary Card */}
      {consistencyResults.size > 0 && (
        <Card className="relative overflow-hidden border-blue-200/50 bg-blue-50/5">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-semibold">数据一致性</CardTitle>
              <Badge className="text-xs bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 hover:bg-blue-100">
                {consistencyResults.size} 个接口已校验
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="pb-3">
            <div className="grid grid-cols-3 gap-y-2 text-sm select-text">
              <div>
                <span className="text-muted-foreground">一致</span>
                <div className="font-semibold text-green-600 mt-0.5">
                  {Array.from(consistencyResults.values()).filter((c) => c.status === "consistent").length}
                </div>
              </div>
              <div>
                <span className="text-muted-foreground">字段缺失</span>
                <div className="font-semibold text-yellow-600 mt-0.5">
                  {Array.from(consistencyResults.values()).filter((c) => c.status === "warn").length}
                </div>
              </div>
              <div>
                <span className="text-muted-foreground">值差异</span>
                <div className="font-semibold text-red-600 mt-0.5">
                  {Array.from(consistencyResults.values()).filter((c) => c.status === "error").length}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={handleRunAll} disabled={running}>
          {running ? `探测中 (${progress}/${total})...` : "全部探测"}
        </Button>
        <Button variant="outline" onClick={loadStats} disabled={loading}>
          刷新统计
        </Button>
        <Select
          value={statusFilter}
          onValueChange={(v) => setStatusFilter(v as StatusFilter)}
        >
          <SelectTrigger className="w-[100px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部</SelectItem>
            <SelectItem value="ok">正常</SelectItem>
            <SelectItem value="error">异常</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={timeRange}
          onValueChange={(v) => setTimeRange(v as TimeRange)}
        >
          <SelectTrigger className="w-[100px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">1 小时</SelectItem>
            <SelectItem value="6">6 小时</SelectItem>
            <SelectItem value="24">24 小时</SelectItem>
            <SelectItem value="168">7 天</SelectItem>
          </SelectContent>
        </Select>
        {running && (
          <div className="flex-1 ml-2">
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-300 rounded-full"
                style={{ width: total > 0 ? `${(progress / total) * 100}%` : "0%" }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Empty state */}
      {!hasAnyData && !running && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground mb-4">
              暂无探测数据，点击「全部探测」开始健康检查
            </p>
            <Button onClick={handleRunAll}>全部探测</Button>
          </CardContent>
        </Card>
      )}

      {/* Recent Errors */}
      {recentErrors.length > 0 && (
        <Card className="border-red-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-red-600">
              异常记录 ({recentErrors.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-1.5">
              {recentErrors.map((e, i) => (
                <div key={i} className="flex items-start gap-2 text-xs select-text">
                  <span className="w-2 h-2 rounded-full bg-red-500 mt-1 flex-shrink-0" />
                  <span className="font-mono text-muted-foreground w-20 flex-shrink-0">
                    {e.provider}
                  </span>
                  <span className="font-mono flex-shrink-0">
                    {e.tool.replace("tool_get_", "")}
                  </span>
                  <span className="text-red-600 flex-1 select-text break-all" title={e.error}>
                    {e.error}
                  </span>
                  <span className="text-muted-foreground flex-shrink-0">
                    {e.time ?? "--"}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Consistency Issues */}
      {(() => {
        const issues = Array.from(consistencyResults.values()).filter(
          (c) => c.status !== "consistent",
        )
        if (issues.length === 0) return null
        return (
          <Card className="border-yellow-200 dark:border-yellow-800/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                数据一致性问题 ({issues.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-3">
                {issues.map((c) => (
                  <div key={c.tool} className="space-y-1">
                    <div className="font-mono text-xs font-semibold select-text">
                      {c.tool.replace("tool_get_", "")}
                      <span className="text-muted-foreground font-normal ml-2">
                        ({c.providers_compared.join(" vs ")})
                      </span>
                    </div>
                    {c.diffs.map((d, i) => (
                      <div key={i} className="flex items-start gap-2 text-xs ml-4 select-text">
                        <span
                          className={`w-2 h-2 rounded-full mt-1 flex-shrink-0 ${
                            d.level === "error" ? "bg-red-500" : "bg-yellow-500"
                          }`}
                        />
                        <span className="font-mono flex-shrink-0">{d.field}</span>
                        <span className="text-muted-foreground">{d.detail}</span>
                        {d.level === "error" && (
                          <span className="text-red-500 font-mono break-all">
                            {Object.entries(d.values)
                              .map(([p, v]) => `${p}=${JSON.stringify(v)}`)
                              .join(", ")}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )
      })()}

      {/* Status Matrix */}
      {(hasAnyData || running) && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">接口状态矩阵</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <ScrollArea className="w-full">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[260px] text-xs sticky left-0 bg-background z-10">
                      领域 / 接口
                    </TableHead>
                    {allProviders.map((p) => (
                      <TableHead key={p} className="text-xs text-center w-[120px]">
                        {p}
                      </TableHead>
                    ))}
                    <TableHead className="text-xs text-center w-[80px]">一致性</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Array.from(domainGroups.entries()).map(([domain, domainTools]) => {
                    const filtered = domainTools.filter(shouldShowTool)
                    if (filtered.length === 0) return null
                    const domainLabel = DOMAIN_LABELS[domain] ?? domain

                    return [
                      // Domain header row
                      <TableRow key={`domain-${domain}`} className="bg-muted/30 hover:bg-muted/30">
                        <TableCell
                          colSpan={allProviders.length + 2}
                          className="py-1.5 text-xs font-semibold text-muted-foreground sticky left-0"
                        >
                          {domainLabel}
                          <span className="font-normal ml-1">({filtered.length})</span>
                        </TableCell>
                      </TableRow>,
                      // Tool rows
                      ...filtered.map((tool) => (
                        <TableRow key={tool.name}>
                          <TableCell className="py-1.5 sticky left-0 bg-background z-10 select-text">
                            <div className="flex items-center gap-1.5 group">
                              <button
                                onClick={() => handleProbeTool(tool.name)}
                                disabled={running || probingTool !== null}
                                className="w-5 h-5 flex-shrink-0 inline-flex items-center justify-center rounded text-muted-foreground/40 hover:text-primary hover:bg-primary/10 opacity-0 group-hover:opacity-100 transition-all disabled:opacity-0 disabled:cursor-not-allowed"
                                title="探测此接口"
                              >
                                {probingTool === tool.name ? (
                                  <svg className="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="32" strokeLinecap="round" /></svg>
                                ) : (
                                  <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z" /></svg>
                                )}
                              </button>
                              <Tooltip>
                                <TooltipTrigger
                                  className="text-xs cursor-help text-left select-text"
                                  render={<span />}
                                >
                                  <span className="font-medium">{tool.display_name ?? tool.description}</span>
                                  <span className="text-muted-foreground ml-1 font-mono text-[10px]">{tool.name.replace("tool_get_", "")}</span>
                                </TooltipTrigger>
                                <TooltipContent side="right" className="max-w-xs">
                                  <p className="font-mono text-xs mb-1 select-text">{tool.name}</p>
                                  <p className="text-xs select-text">{tool.description}</p>
                                  {tool.return_fields.length > 0 && (
                                    <p className="text-xs text-muted-foreground mt-1 select-text">
                                      字段: {tool.return_fields.join(", ")}
                                    </p>
                                  )}
                                </TooltipContent>
                              </Tooltip>
                            </div>
                          </TableCell>
                          {allProviders.map((provider) => {
                            const hasProvider = tool.providers.includes(provider)
                            if (!hasProvider) {
                              return (
                                <TableCell key={provider} className="text-center py-1.5">
                                  <span className="text-xs text-muted-foreground/30">--</span>
                                </TableCell>
                              )
                            }
                            const { status, timeMs, stat, isLive } = getStatus(tool.name, provider)
                            return (
                              <TableCell key={provider} className="text-center py-1.5">
                                <StatusCell
                                  status={status}
                                  timeMs={timeMs}
                                  stat={stat ?? undefined}
                                  isLive={isLive}
                                />
                              </TableCell>
                            )
                          })}
                          <TableCell className="text-center py-1.5">
                            <ConsistencyBadge result={consistencyResults.get(tool.name)} />
                          </TableCell>
                        </TableRow>
                      )),
                    ]
                  })}
                </TableBody>
              </Table>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {loading && stats.length === 0 && !running && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      )}
    </div>
  )
}

/** Consistency badge for a tool row */
function ConsistencyBadge({ result }: { result?: ConsistencyResult }) {
  if (!result) {
    return <span className="text-xs text-muted-foreground/30">--</span>
  }

  if (result.status === "consistent") {
    return (
      <Tooltip>
        <TooltipTrigger render={<span />} className="select-text">
          <span className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 bg-green-50 dark:bg-green-950/20">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
            <span className="text-xs">一致</span>
          </span>
        </TooltipTrigger>
        <TooltipContent>
          <div className="text-xs select-text">
            比较: {result.providers_compared.join(", ")}
          </div>
        </TooltipContent>
      </Tooltip>
    )
  }

  const warnCount = result.diffs.filter((d) => d.level === "warn").length
  const errorCount = result.diffs.filter((d) => d.level === "error").length
  const isError = result.status === "error"

  return (
    <Tooltip>
      <TooltipTrigger render={<span />} className="select-text">
        <span
          className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 ${
            isError
              ? "bg-red-50 dark:bg-red-950/20"
              : "bg-yellow-50 dark:bg-yellow-950/20"
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isError ? "bg-red-500" : "bg-yellow-500"
            }`}
          />
          <span className="text-xs">
            {errorCount > 0 ? `${errorCount}差异` : `${warnCount}缺失`}
          </span>
        </span>
      </TooltipTrigger>
      <TooltipContent side="left" className="max-w-md">
        <div className="text-xs space-y-1 select-text">
          <div>比较: {result.providers_compared.join(", ")}</div>
          {result.diffs.slice(0, 8).map((d, i) => (
            <div key={i} className="flex gap-2">
              <span
                className={
                  d.level === "error" ? "text-red-400" : "text-yellow-400"
                }
              >
                {d.level === "error" ? "差异" : "缺失"}
              </span>
              <span className="font-mono">{d.field}</span>
              <span className="text-muted-foreground">{d.detail}</span>
            </div>
          ))}
          {result.diffs.length > 8 && (
            <div className="text-muted-foreground">...+{result.diffs.length - 8} 项</div>
          )}
        </div>
      </TooltipContent>
    </Tooltip>
  )
}

/** A single cell in the status matrix */
function StatusCell({
  status,
  timeMs,
  stat,
  isLive,
}: {
  status: string | null
  timeMs: number | null
  stat?: ToolStats
  isLive: boolean
}) {
  if (!status) {
    return <span className="text-xs text-muted-foreground/50">未检测</span>
  }

  const dotColor =
    status === "ok" ? "bg-green-500"
      : status === "warn" ? "bg-yellow-500"
      : status === "timeout" ? "bg-orange-500"
      : "bg-red-500"
  const bgColor =
    status === "ok"
      ? "bg-green-50 dark:bg-green-950/20"
      : status === "warn"
        ? "bg-yellow-50 dark:bg-yellow-950/20"
        : status === "timeout"
          ? "bg-orange-50 dark:bg-orange-950/20"
          : "bg-red-50 dark:bg-red-950/20"

  const content = (
    <div
      className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 ${bgColor} ${
        isLive ? "ring-1 ring-primary/30 animate-in fade-in duration-300" : ""
      }`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <span className="text-xs font-mono">
        {timeMs != null ? `${timeMs.toFixed(0)}ms` : status === "ok" ? "OK" : "ERR"}
      </span>
    </div>
  )

  if (stat) {
    return (
      <Tooltip>
        <TooltipTrigger render={<span />} className="select-text">{content}</TooltipTrigger>
        <TooltipContent>
          <div className="text-xs space-y-0.5 select-text">
            <div>成功率: {stat.success_rate}%</div>
            <div>调用次数: {stat.total_calls}</div>
            <div>平均耗时: {stat.avg_response_ms.toFixed(0)}ms</div>
            {stat.last_check_time && (
              <div>最后检测: {timeAgo(stat.last_check_time)}</div>
            )}
            {stat.last_error && <div className="text-red-400 break-all max-w-[300px]">{stat.last_error}</div>}
          </div>
        </TooltipContent>
      </Tooltip>
    )
  }

  return content
}

function timeAgo(ts: string): string {
  const date = new Date(ts)
  const now = Date.now()
  const diff = now - date.getTime()
  if (diff < 0) return "刚刚"
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return `${seconds}秒前`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  return `${days}天前`
}
