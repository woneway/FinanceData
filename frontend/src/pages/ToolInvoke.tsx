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

// Known parameters for each tool (matching backend _get_test_params)
const TOOL_PARAMS: Record<string, { key: string; label: string; placeholder: string }[]> = {
  tool_get_stock_info_history: [{ key: "symbol", label: "Symbol", placeholder: "e.g. 000001" }],
  tool_get_kline_history: [
    { key: "symbol", label: "Symbol", placeholder: "e.g. 000001" },
    { key: "period", label: "Period", placeholder: "daily/weekly/monthly" },
    { key: "start", label: "Start Date", placeholder: "YYYYMMDD" },
    { key: "end", label: "End Date", placeholder: "YYYYMMDD" },
    { key: "adj", label: "Adjust", placeholder: "qfq/hfq/empty" },
  ],
  tool_get_realtime_quote: [{ key: "symbol", label: "Symbol", placeholder: "e.g. 000001" }],
  tool_get_index_quote_realtime: [{ key: "symbol", label: "Symbol", placeholder: "e.g. 000001.SH" }],
  tool_get_index_history: [
    { key: "symbol", label: "Symbol", placeholder: "e.g. 000001.SH" },
    { key: "start", label: "Start Date", placeholder: "YYYYMMDD" },
    { key: "end", label: "End Date", placeholder: "YYYYMMDD" },
  ],
  tool_get_sector_rank_realtime: [],
  tool_get_chip_distribution_history: [{ key: "symbol", label: "Symbol", placeholder: "e.g. 000001" }],
  tool_get_financial_summary_history: [{ key: "symbol", label: "Symbol", placeholder: "e.g. 000001" }],
  tool_get_dividend_history: [{ key: "symbol", label: "Symbol", placeholder: "e.g. 000001" }],
  tool_get_earnings_forecast_history: [{ key: "symbol", label: "Symbol", placeholder: "e.g. 000001" }],
  tool_get_stock_capital_flow_realtime: [{ key: "symbol", label: "Symbol", placeholder: "e.g. 000001" }],
  tool_get_trade_calendar_history: [
    { key: "start", label: "Start Date", placeholder: "YYYYMMDD" },
    { key: "end", label: "End Date", placeholder: "YYYYMMDD" },
  ],
  tool_get_lhb_detail: [
    { key: "start_date", label: "Start Date", placeholder: "YYYYMMDD" },
    { key: "end_date", label: "End Date", placeholder: "YYYYMMDD" },
  ],
  tool_get_lhb_stock_stat: [{ key: "period", label: "Period", placeholder: "近一月/近三月/近六月/近一年" }],
  tool_get_lhb_active_traders: [
    { key: "start_date", label: "Start Date", placeholder: "YYYYMMDD" },
    { key: "end_date", label: "End Date", placeholder: "YYYYMMDD" },
  ],
  tool_get_lhb_trader_stat: [{ key: "period", label: "Period", placeholder: "近一月/近三月/近六月/近一年" }],
  tool_get_lhb_stock_detail: [
    { key: "symbol", label: "Symbol", placeholder: "e.g. 600077" },
    { key: "date", label: "Date", placeholder: "YYYYMMDD" },
    { key: "flag", label: "Flag", placeholder: "买入/卖出" },
  ],
  tool_get_zt_pool: [{ key: "date", label: "Date", placeholder: "YYYYMMDD" }],
  tool_get_strong_stocks: [{ key: "date", label: "Date", placeholder: "YYYYMMDD" }],
  tool_get_previous_zt: [{ key: "date", label: "Date", placeholder: "YYYYMMDD" }],
  tool_get_zbgc_pool: [{ key: "date", label: "Date", placeholder: "YYYYMMDD" }],
  tool_get_north_stock_hold: [
    { key: "market", label: "Market", placeholder: "沪股通/深股通" },
    { key: "indicator", label: "Indicator", placeholder: "5日排行/10日排行/..." },
  ],
  tool_get_margin: [{ key: "trade_date", label: "Trade Date", placeholder: "YYYYMMDD" }],
  tool_get_margin_detail: [{ key: "trade_date", label: "Trade Date", placeholder: "YYYYMMDD" }],
  tool_get_market_stats_realtime: [],
  tool_get_market_north_capital: [],
  tool_get_sector_capital_flow: [
    { key: "indicator", label: "Indicator", placeholder: "今日/5日/10日" },
    { key: "sector_type", label: "Sector Type", placeholder: "行业资金流/概念资金流/地域资金流" },
  ],
}

interface ToolInvokeProps {
  tools: ToolInfo[]
}

export default function ToolInvoke({ tools }: ToolInvokeProps) {
  const [search, setSearch] = useState("")
  const [selectedTool, setSelectedTool] = useState<string>("")
  const [params, setParams] = useState<Record<string, string>>({})
  const [invoking, setInvoking] = useState(false)
  const [result, setResult] = useState<InvokeResponse | null>(null)

  const filteredTools = search
    ? tools.filter(
        (t) =>
          t.name.toLowerCase().includes(search.toLowerCase()) ||
          t.description.toLowerCase().includes(search.toLowerCase()) ||
          t.domain.toLowerCase().includes(search.toLowerCase()),
      )
    : tools

  const selectedToolInfo = tools.find((t) => t.name === selectedTool)
  const paramDefs = TOOL_PARAMS[selectedTool] ?? []

  const handleSelectTool = (name: string) => {
    setSelectedTool(name)
    setParams({})
    setResult(null)
  }

  const handleSubmit = async () => {
    if (!selectedTool) return
    setInvoking(true)
    setResult(null)
    try {
      // Filter out empty params
      const cleanParams: Record<string, string> = {}
      for (const [k, v] of Object.entries(params)) {
        if (v.trim()) cleanParams[k] = v.trim()
      }
      const res = await invokeTool(selectedTool, cleanParams)
      setResult(res)
    } catch (e) {
      setResult({
        tool: selectedTool,
        provider: "unknown",
        status: "error",
        response_time_ms: 0,
        data: null,
        error: String(e),
      })
    } finally {
      setInvoking(false)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
      {/* Tool selector */}
      <div className="space-y-3">
        <Input
          placeholder="Search tools..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <ScrollArea className="h-[600px] rounded-md border">
          <div className="p-2 space-y-1">
            {filteredTools.map((tool) => (
              <button
                key={tool.name}
                onClick={() => handleSelectTool(tool.name)}
                className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                  selectedTool === tool.name
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-muted"
                }`}
              >
                <div className="font-mono text-xs">{tool.name}</div>
                <div className="text-xs opacity-70 mt-0.5 truncate">
                  {tool.description}
                </div>
                <Badge variant="secondary" className="mt-1 text-[10px]">
                  {tool.domain}
                </Badge>
              </button>
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
                <CardTitle className="text-base font-mono">
                  {selectedToolInfo.name}
                </CardTitle>
                <p className="text-sm text-muted-foreground">
                  {selectedToolInfo.description}
                </p>
                <div className="flex gap-2 pt-1">
                  <Badge variant="secondary">{selectedToolInfo.domain}</Badge>
                  <Badge variant="outline">
                    {selectedToolInfo.providers.join(", ")}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                {paramDefs.length > 0 ? (
                  <div className="space-y-3">
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
                    No parameters required
                  </p>
                )}
                <Button
                  className="mt-4"
                  onClick={handleSubmit}
                  disabled={invoking}
                >
                  {invoking ? "Invoking..." : "Invoke"}
                </Button>
              </CardContent>
            </Card>

            {/* Result */}
            {invoking && <Skeleton className="h-40 w-full" />}
            {result && <ResultDisplay result={result} />}
          </>
        ) : (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              Select a tool from the list to get started
            </CardContent>
          </Card>
        )}
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
          <CardTitle className="text-base">Result</CardTitle>
          <Badge
            className={
              result.status === "ok"
                ? "bg-green-600 text-white hover:bg-green-600"
                : "bg-red-600 text-white hover:bg-red-600"
            }
          >
            {result.status}
          </Badge>
          <span className="text-sm text-muted-foreground">
            Provider: {result.provider} | {result.response_time_ms}ms
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
          Showing 100 of {rows.length} rows
        </p>
      )}
    </ScrollArea>
  )
}
