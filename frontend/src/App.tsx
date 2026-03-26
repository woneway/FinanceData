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
          : "border-red-600 text-red-600"
      }
      title={p.reason}
    >
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
        <header className="border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold">FinanceData Dashboard</h1>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground mr-2">
                Providers:
              </span>
              {providers.map(providerBadge)}
            </div>
          </div>
        </header>

        {/* Main */}
        <main className="p-6">
          <Tabs defaultValue="health">
            <TabsList>
              <TabsTrigger value="health">Health Check</TabsTrigger>
              <TabsTrigger value="invoke">Tool Invoke</TabsTrigger>
            </TabsList>
            <TabsContent value="health" className="mt-4">
              <HealthCheck tools={tools} />
            </TabsContent>
            <TabsContent value="invoke" className="mt-4">
              <ToolInvoke tools={tools} />
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </TooltipProvider>
  )
}

export default App
