import { useCallback, useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
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
import {
  type HealthResult,
  type ToolInfo,
  type ToolStats,
  fetchStats,
  runHealthCheck,
} from "@/lib/api"

type StatusFilter = "all" | "ok" | "error"
type TimeRange = "1" | "6" | "24" | "168"

function statusBadge(status: string | null) {
  if (!status) return <Badge variant="secondary">--</Badge>
  if (status === "ok")
    return (
      <Badge className="bg-green-600 text-white hover:bg-green-600">OK</Badge>
    )
  if (status === "timeout")
    return (
      <Badge className="bg-yellow-500 text-white hover:bg-yellow-500">
        Timeout
      </Badge>
    )
  return (
    <Badge className="bg-red-600 text-white hover:bg-red-600">Error</Badge>
  )
}

interface HealthCheckProps {
  tools: ToolInfo[]
}

export default function HealthCheck({ tools }: HealthCheckProps) {
  const [stats, setStats] = useState<ToolStats[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [liveResults, setLiveResults] = useState<Map<string, HealthResult>>(
    new Map(),
  )
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all")
  const [timeRange, setTimeRange] = useState<TimeRange>("24")
  const [openDomains, setOpenDomains] = useState<Set<string>>(new Set())

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

  useEffect(() => {
    loadStats()
  }, [loadStats])

  const handleRunAll = async () => {
    setRunning(true)
    setLiveResults(new Map())
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
          setRunning(false)
          loadStats()
        },
      )
    } catch (e) {
      console.error("Health check failed:", e)
      setRunning(false)
    }
  }

  // Build domain -> tool groups
  const domainGroups = new Map<string, ToolInfo[]>()
  for (const tool of tools) {
    const group = domainGroups.get(tool.domain) ?? []
    group.push(tool)
    domainGroups.set(tool.domain, group)
  }

  // Build stats lookup
  const statsLookup = new Map<string, ToolStats>()
  for (const s of stats) {
    statsLookup.set(`${s.tool}:${s.provider}`, s)
  }

  // Summary calculations
  const totalTools = tools.length
  const totalProbes = stats.reduce((sum, s) => sum + s.total_calls, 0)
  const totalSuccess = stats.reduce((sum, s) => sum + s.success_count, 0)
  const successRate =
    totalProbes > 0 ? ((totalSuccess / totalProbes) * 100).toFixed(1) : "--"
  const avgTime =
    stats.length > 0
      ? (
          stats.reduce((sum, s) => sum + s.avg_response_ms, 0) / stats.length
        ).toFixed(0)
      : "--"
  const errorCount = stats.filter((s) => s.last_status === "error").length

  // Filter logic
  const shouldShowTool = (tool: ToolInfo) => {
    if (statusFilter === "all") return true
    for (const provider of tool.providers) {
      const key = `${tool.name}:${provider}`
      const live = liveResults.get(key)
      const stat = statsLookup.get(key)
      const status = live?.status ?? stat?.last_status
      if (statusFilter === "ok" && status === "ok") return true
      if (statusFilter === "error" && status !== "ok" && status != null)
        return true
    }
    return false
  }

  const toggleDomain = (domain: string) => {
    setOpenDomains((prev) => {
      const next = new Set(prev)
      if (next.has(domain)) next.delete(domain)
      else next.add(domain)
      return next
    })
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Tools
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTools}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Probes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalProbes}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Success Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{successRate}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Avg Time
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgTime}ms</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Errors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{errorCount}</div>
          </CardContent>
        </Card>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={handleRunAll} disabled={running}>
          {running ? "Running..." : "Run All"}
        </Button>
        <Button variant="outline" onClick={loadStats} disabled={loading}>
          Refresh Stats
        </Button>
        <Select
          value={statusFilter}
          onValueChange={(v) => setStatusFilter(v as StatusFilter)}
        >
          <SelectTrigger className="w-[120px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="ok">OK</SelectItem>
            <SelectItem value="error">Error</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={timeRange}
          onValueChange={(v) => setTimeRange(v as TimeRange)}
        >
          <SelectTrigger className="w-[120px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">1h</SelectItem>
            <SelectItem value="6">6h</SelectItem>
            <SelectItem value="24">24h</SelectItem>
            <SelectItem value="168">7d</SelectItem>
          </SelectContent>
        </Select>
        {running && (
          <span className="text-sm text-muted-foreground">
            {liveResults.size} results received...
          </span>
        )}
      </div>

      {/* Domain Groups */}
      {loading && stats.length === 0 ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : (
        Array.from(domainGroups.entries()).map(([domain, domainTools]) => {
          const filteredTools = domainTools.filter(shouldShowTool)
          if (filteredTools.length === 0) return null

          return (
            <Collapsible
              key={domain}
              open={openDomains.has(domain)}
              onOpenChange={() => toggleDomain(domain)}
            >
              <CollapsibleTrigger className="flex w-full items-center justify-between rounded-md px-4 py-3 text-left hover:bg-muted">
                  <span className="font-semibold capitalize">
                    {domain}{" "}
                    <span className="text-muted-foreground font-normal">
                      ({filteredTools.length} tools)
                    </span>
                  </span>
                  <span className="text-muted-foreground">
                    {openDomains.has(domain) ? "\u25B2" : "\u25BC"}
                  </span>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="space-y-3 pb-2">
                  {filteredTools.map((tool) => (
                    <ToolRow
                      key={tool.name}
                      tool={tool}
                      statsLookup={statsLookup}
                      liveResults={liveResults}
                    />
                  ))}
                </div>
              </CollapsibleContent>
            </Collapsible>
          )
        })
      )}
    </div>
  )
}

function ToolRow({
  tool,
  statsLookup,
  liveResults,
}: {
  tool: ToolInfo
  statsLookup: Map<string, ToolStats>
  liveResults: Map<string, HealthResult>
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-mono">{tool.name}</CardTitle>
        <p className="text-xs text-muted-foreground">{tool.description}</p>
      </CardHeader>
      <CardContent className="pt-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">Provider</TableHead>
              <TableHead className="w-[80px]">Status</TableHead>
              <TableHead className="w-[100px]">Time (ms)</TableHead>
              <TableHead className="w-[100px]">Success Rate</TableHead>
              <TableHead className="w-[80px]">Calls</TableHead>
              <TableHead>Last Check</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tool.providers.map((provider) => {
              const key = `${tool.name}:${provider}`
              const stat = statsLookup.get(key)
              const live = liveResults.get(key)
              const status = live?.status ?? stat?.last_status
              const timeMs = live?.response_time_ms ?? stat?.avg_response_ms
              const lastCheck = stat?.last_check_time
                ? new Date(stat.last_check_time).toLocaleTimeString()
                : "--"

              return (
                <TableRow
                  key={provider}
                  className={
                    live ? "animate-in fade-in duration-300" : undefined
                  }
                >
                  <TableCell className="font-medium">{provider}</TableCell>
                  <TableCell>{statusBadge(status ?? null)}</TableCell>
                  <TableCell>
                    {timeMs != null ? `${timeMs.toFixed(0)}` : "--"}
                  </TableCell>
                  <TableCell>
                    {stat ? `${stat.success_rate}%` : "--"}
                  </TableCell>
                  <TableCell>{stat?.total_calls ?? 0}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {live ? "just now" : lastCheck}
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
