import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
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
import { type InvokeResponse, type ToolInfo, invokeTool } from "@/lib/api"

const DOMAIN_LABELS: Record<string, string> = {
  stock: "个股信息",
  kline: "K线数据",
  realtime: "实时行情",
  index: "指数数据",
  sector: "板块排名",
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
}

// Known parameters for each tool (matching backend _get_test_params)
const TOOL_PARAMS: Record<string, { key: string; label: string; placeholder: string }[]> = {
  tool_get_stock_info_history: [{ key: "symbol", label: "股票代码", placeholder: "如 000001" }],
  tool_get_kline_history: [
    { key: "symbol", label: "股票代码", placeholder: "如 000001" },
    { key: "period", label: "周期", placeholder: "daily/weekly/monthly" },
    { key: "start", label: "开始日期", placeholder: "YYYYMMDD" },
    { key: "end", label: "结束日期", placeholder: "YYYYMMDD" },
    { key: "adj", label: "复权方式", placeholder: "qfq(前复权)/hfq(后复权)/留空" },
  ],
  tool_get_realtime_quote: [{ key: "symbol", label: "股票代码", placeholder: "如 000001" }],
  tool_get_index_quote_realtime: [{ key: "symbol", label: "指数代码", placeholder: "如 000001.SH" }],
  tool_get_index_history: [
    { key: "symbol", label: "指数代码", placeholder: "如 000001.SH" },
    { key: "start", label: "开始日期", placeholder: "YYYYMMDD" },
    { key: "end", label: "结束日期", placeholder: "YYYYMMDD" },
  ],
  tool_get_sector_rank_realtime: [],
  tool_get_chip_distribution_history: [{ key: "symbol", label: "股票代码", placeholder: "如 000001" }],
  tool_get_financial_summary_history: [{ key: "symbol", label: "股票代码", placeholder: "如 000001" }],
  tool_get_dividend_history: [{ key: "symbol", label: "股票代码", placeholder: "如 000001" }],
  tool_get_earnings_forecast_history: [{ key: "symbol", label: "股票代码", placeholder: "如 000001" }],
  tool_get_stock_capital_flow_realtime: [{ key: "symbol", label: "股票代码", placeholder: "如 000001" }],
  tool_get_trade_calendar_history: [
    { key: "start", label: "开始日期", placeholder: "YYYYMMDD" },
    { key: "end", label: "结束日期", placeholder: "YYYYMMDD" },
  ],
  tool_get_lhb_detail: [
    { key: "start_date", label: "开始日期", placeholder: "YYYYMMDD" },
    { key: "end_date", label: "结束日期", placeholder: "YYYYMMDD" },
  ],
  tool_get_lhb_stock_stat: [{ key: "period", label: "统计周期", placeholder: "近一月/近三月/近六月/近一年" }],
  tool_get_lhb_active_traders: [
    { key: "start_date", label: "开始日期", placeholder: "YYYYMMDD" },
    { key: "end_date", label: "结束日期", placeholder: "YYYYMMDD" },
  ],
  tool_get_lhb_trader_stat: [{ key: "period", label: "统计周期", placeholder: "近一月/近三月/近六月/近一年" }],
  tool_get_lhb_stock_detail: [
    { key: "symbol", label: "股票代码", placeholder: "如 600077" },
    { key: "date", label: "日期", placeholder: "YYYYMMDD" },
    { key: "flag", label: "方向", placeholder: "买入/卖出" },
  ],
  tool_get_zt_pool: [{ key: "date", label: "日期", placeholder: "YYYYMMDD" }],
  tool_get_strong_stocks: [{ key: "date", label: "日期", placeholder: "YYYYMMDD" }],
  tool_get_previous_zt: [{ key: "date", label: "日期", placeholder: "YYYYMMDD" }],
  tool_get_zbgc_pool: [{ key: "date", label: "日期", placeholder: "YYYYMMDD" }],
  tool_get_north_stock_hold: [
    { key: "market", label: "市场", placeholder: "沪股通/深股通" },
    { key: "indicator", label: "排行指标", placeholder: "5日排行/10日排行/..." },
  ],
  tool_get_margin: [{ key: "trade_date", label: "交易日期", placeholder: "YYYYMMDD" }],
  tool_get_margin_detail: [{ key: "trade_date", label: "交易日期", placeholder: "YYYYMMDD" }],
  tool_get_market_stats_realtime: [],
  tool_get_market_north_capital: [],
  tool_get_sector_capital_flow: [
    { key: "indicator", label: "时间范围", placeholder: "今日/5日/10日" },
    { key: "sector_type", label: "板块类型", placeholder: "行业资金流/概念资金流/地域资金流" },
  ],
}

interface ToolInvokeProps {
  tools: ToolInfo[]
}

export default function ToolInvoke({ tools }: ToolInvokeProps) {
  const [search, setSearch] = useState("")
  const [selectedTool, setSelectedTool] = useState<string>("")
  const [params, setParams] = useState<Record<string, string>>({})
  const [selectedProviders, setSelectedProviders] = useState<Set<string>>(new Set())
  const [invoking, setInvoking] = useState(false)
  const [results, setResults] = useState<Map<string, InvokeResponse>>(new Map())

  const filteredTools = search
    ? tools.filter(
        (t) =>
          t.name.toLowerCase().includes(search.toLowerCase()) ||
          t.description.toLowerCase().includes(search.toLowerCase()) ||
          t.domain.toLowerCase().includes(search.toLowerCase()),
      )
    : tools

  // Group by domain
  const domainGroups = new Map<string, ToolInfo[]>()
  for (const tool of filteredTools) {
    const group = domainGroups.get(tool.domain) ?? []
    group.push(tool)
    domainGroups.set(tool.domain, group)
  }

  const selectedToolInfo = tools.find((t) => t.name === selectedTool)
  const paramDefs = TOOL_PARAMS[selectedTool] ?? []

  const handleSelectTool = (name: string) => {
    setSelectedTool(name)
    setParams({})
    setSelectedProviders(new Set())
    setResults(new Map())
  }

  const toggleProvider = (provider: string) => {
    setSelectedProviders((prev) => {
      const next = new Set(prev)
      if (next.has(provider)) next.delete(provider)
      else next.add(provider)
      return next
    })
  }

  const handleSubmit = async () => {
    if (!selectedTool) return
    setInvoking(true)
    setResults(new Map())

    const cleanParams: Record<string, string> = {}
    for (const [k, v] of Object.entries(params)) {
      if (v.trim()) cleanParams[k] = v.trim()
    }

    const calls: { key: string; provider?: string }[] = []
    if (selectedProviders.size === 0) {
      calls.push({ key: "auto" })
    } else {
      for (const p of selectedProviders) {
        calls.push({ key: p, provider: p })
      }
    }

    const promises = calls.map(async ({ key, provider }) => {
      try {
        const res = await invokeTool(selectedTool, cleanParams, provider)
        return { key, res }
      } catch (e) {
        return {
          key,
          res: {
            tool: selectedTool,
            provider: provider ?? "unknown",
            status: "error" as const,
            response_time_ms: 0,
            data: null,
            error: String(e),
          },
        }
      }
    })

    const settled = await Promise.all(promises)
    const newResults = new Map<string, InvokeResponse>()
    for (const { key, res } of settled) {
      newResults.set(key, res)
    }
    setResults(newResults)
    setInvoking(false)
  }

  const isCompareMode = selectedProviders.size > 1

  return (
    <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
      {/* Tool selector */}
      <div className="space-y-3">
        <Input
          placeholder="搜索工具名称、描述或领域..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <ScrollArea className="h-[600px] rounded-md border">
          <div className="p-2 space-y-3">
            {Array.from(domainGroups.entries()).map(([domain, domainTools]) => (
              <div key={domain}>
                <div className="px-2 py-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {DOMAIN_LABELS[domain] ?? domain}
                  <span className="ml-1 font-normal normal-case">({domainTools.length})</span>
                </div>
                <div className="space-y-0.5">
                  {domainTools.map((tool) => (
                    <button
                      key={tool.name}
                      onClick={() => handleSelectTool(tool.name)}
                      className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                        selectedTool === tool.name
                          ? "bg-primary text-primary-foreground"
                          : "hover:bg-muted"
                      }`}
                    >
                      <div className="font-mono text-xs">{tool.name.replace("tool_get_", "")}</div>
                      <div className="text-xs opacity-70 mt-0.5 truncate">
                        {tool.description}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Parameter form + results */}
      <div className="space-y-4">
        {selectedToolInfo ? (
          <>
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <CardTitle className="text-base font-mono">
                    {selectedToolInfo.name}
                  </CardTitle>
                  <Badge variant="secondary" className="text-[10px]">
                    {DOMAIN_LABELS[selectedToolInfo.domain] ?? selectedToolInfo.domain}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  {selectedToolInfo.description}
                </p>
                {/* Provider multi-select */}
                <div className="flex flex-wrap items-center gap-2 pt-2">
                  <span className="text-xs text-muted-foreground">数据源:</span>
                  {selectedToolInfo.providers.map((p) => (
                    <button
                      key={p}
                      onClick={() => toggleProvider(p)}
                      className={`inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-medium transition-colors cursor-pointer ${
                        selectedProviders.has(p)
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border hover:bg-muted"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                  {selectedProviders.size > 0 && (
                    <button
                      onClick={() => setSelectedProviders(new Set())}
                      className="text-xs text-muted-foreground hover:text-foreground underline"
                    >
                      清除
                    </button>
                  )}
                  <span className="text-xs text-muted-foreground ml-1">
                    {selectedProviders.size === 0
                      ? "(自动选择最优数据源)"
                      : selectedProviders.size > 1
                        ? `(已选 ${selectedProviders.size} 个，对比模式)`
                        : ""}
                  </span>
                </div>
                {selectedToolInfo.providers.length > 1 && (
                  <button
                    onClick={() =>
                      setSelectedProviders(new Set(selectedToolInfo.providers))
                    }
                    className="text-xs text-muted-foreground hover:text-foreground underline w-fit"
                  >
                    全选对比
                  </button>
                )}
              </CardHeader>
              <CardContent>
                {paramDefs.length > 0 ? (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {paramDefs.map((p) => (
                      <div key={p.key} className="space-y-1">
                        <label className="text-sm font-medium">{p.label}</label>
                        <Input
                          placeholder={p.placeholder}
                          value={params[p.key] ?? ""}
                          onChange={(e) =>
                            setParams((prev) => ({
                              ...prev,
                              [p.key]: e.target.value,
                            }))
                          }
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    无需参数，直接调用
                  </p>
                )}
                <Button
                  className="mt-4"
                  onClick={handleSubmit}
                  disabled={invoking}
                >
                  {invoking
                    ? "调用中..."
                    : isCompareMode
                      ? `对比 ${selectedProviders.size} 个数据源`
                      : "调用"}
                </Button>
              </CardContent>
            </Card>

            {/* Results */}
            {invoking && (
              <div className={isCompareMode ? "grid gap-4 grid-cols-1 lg:grid-cols-2" : ""}>
                {Array.from({ length: Math.max(1, selectedProviders.size) }).map((_, i) => (
                  <Skeleton key={i} className="h-40 w-full" />
                ))}
              </div>
            )}
            {results.size > 0 && (
              isCompareMode ? (
                <CompareView results={results} />
              ) : (
                <ResultDisplay result={Array.from(results.values())[0]} />
              )
            )}
          </>
        ) : (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              <p className="text-lg mb-1">从左侧选择一个工具开始</p>
              <p className="text-sm">支持多数据源对比调用</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

/** Side-by-side comparison of multiple provider results */
function CompareView({ results }: { results: Map<string, InvokeResponse> }) {
  const entries = Array.from(results.entries())

  return (
    <div className="space-y-4">
      {/* Summary comparison bar */}
      <Card>
        <CardContent className="py-3">
          <div className="flex flex-wrap gap-4">
            {entries.map(([key, r]) => (
              <div key={key} className="flex items-center gap-2">
                <Badge
                  className={
                    r.status === "ok"
                      ? "bg-green-600 text-white hover:bg-green-600"
                      : "bg-red-600 text-white hover:bg-red-600"
                  }
                >
                  {r.provider}
                </Badge>
                <span className="text-sm font-mono">
                  {r.status === "ok" ? `${r.response_time_ms}ms` : "异常"}
                </span>
                {r.status === "ok" && r.data != null && (
                  <span className="text-xs text-muted-foreground">
                    {(r.data as { data?: unknown[] })?.data?.length ?? 0} 行
                  </span>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Side-by-side results */}
      <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
        {entries.map(([key, r]) => (
          <ResultDisplay key={key} result={r} />
        ))}
      </div>
    </div>
  )
}

function ResultDisplay({ result }: { result: InvokeResponse }) {
  const data = result.data as
    | { data?: unknown[]; source?: string; meta?: unknown }
    | null

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-3">
          <CardTitle className="text-base">
            {result.provider}
          </CardTitle>
          <Badge
            className={
              result.status === "ok"
                ? "bg-green-600 text-white hover:bg-green-600"
                : "bg-red-600 text-white hover:bg-red-600"
            }
          >
            {result.status === "ok" ? "正常" : "异常"}
          </Badge>
          <span className="text-sm text-muted-foreground">
            {result.response_time_ms}ms
            {data?.data && Array.isArray(data.data) && ` | ${data.data.length} 行`}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {result.error && (
          <p className="text-sm text-red-600 mb-3">{result.error}</p>
        )}
        {data?.data && Array.isArray(data.data) && data.data.length > 0 ? (
          <DataTable rows={data.data as Record<string, unknown>[]} />
        ) : (
          <ScrollArea className="h-[300px]">
            <pre className="text-xs bg-muted p-3 rounded-md overflow-auto">
              {JSON.stringify(result.data, null, 2)}
            </pre>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}

function DataTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (rows.length === 0) return null
  const columns = Object.keys(rows[0])
  const displayRows = rows.slice(0, 100)

  return (
    <ScrollArea className="h-[400px]">
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((col) => (
              <TableHead key={col} className="text-xs whitespace-nowrap">
                {col}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {displayRows.map((row, i) => (
            <TableRow key={i}>
              {columns.map((col) => (
                <TableCell key={col} className="text-xs whitespace-nowrap">
                  {String(row[col] ?? "")}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {rows.length > 100 && (
        <p className="text-xs text-muted-foreground p-2 text-center">
          显示前 100 行，共 {rows.length} 行
        </p>
      )}
    </ScrollArea>
  )
}
