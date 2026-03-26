import { useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { TooltipProvider } from "@/components/ui/tooltip"
import { type ProviderStatus, type ToolInfo, fetchProviders, fetchTools } from "@/lib/api"
import HealthCheck from "@/pages/HealthCheck"
import ToolInvoke from "@/pages/ToolInvoke"

function providerBadge(p: ProviderStatus) {
  return (
    <Badge
      key={p.name}
      variant="outline"
      className={
        p.available
          ? "border-green-600 text-green-600"
          : "border-red-400 text-red-400"
      }
      title={p.reason}
    >
      <span
        className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 ${
          p.available ? "bg-green-500" : "bg-red-400"
        }`}
      />
      {p.name}
    </Badge>
  )
}

function App() {
  const [providers, setProviders] = useState<ProviderStatus[]>([])
  const [tools, setTools] = useState<ToolInfo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function init() {
      try {
        const [p, t] = await Promise.all([fetchProviders(), fetchTools()])
        setProviders(p)
        setTools(t)
      } catch (e) {
        console.error("Failed to initialize:", e)
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6 space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    )
  }

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background text-foreground">
        {/* Header */}
        <header className="border-b bg-card px-6 py-4">
          <div className="flex items-center justify-between max-w-screen-xl mx-auto">
            <div>
              <h1 className="text-xl font-bold tracking-tight">FinanceData 数据看板</h1>
              <p className="text-xs text-muted-foreground mt-0.5">
                {tools.length} 个工具 · {providers.filter((p) => p.available).length}/{providers.length} 数据源可用
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground mr-1">数据源</span>
              {providers.map(providerBadge)}
            </div>
          </div>
        </header>

        {/* Main */}
        <main className="p-6 max-w-screen-xl mx-auto">
          <Tabs defaultValue="health">
            <TabsList className="mb-4">
              <TabsTrigger value="health">健康监控</TabsTrigger>
              <TabsTrigger value="invoke">工具调用</TabsTrigger>
            </TabsList>
            <TabsContent value="health" className="mt-0">
              <HealthCheck tools={tools} />
            </TabsContent>
            <TabsContent value="invoke" className="mt-0">
              <ToolInvoke tools={tools} />
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </TooltipProvider>
  )
}

export default App
