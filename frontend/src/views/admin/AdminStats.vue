<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { VisXYContainer, VisStackedBar, VisAxis, VisTooltip, VisBulletLegend } from "@unovis/vue"
import { getStats } from "@/api/stats"
import Card from "@/components/ui/card/Card.vue"

type ChartItem = {
  model: string
  input_cost: number
  output_cost: number
  embedding_cost: number
  gpu_server: number
  database: number
  total: number
}

// Component keys we stack, and their display labels/colors
const components = [
  { key: "input_cost", label: "Input tokens", color: "red" },
  { key: "output_cost", label: "Output tokens", color: "blue" },
  { key: "embedding_cost", label: "Embeddings", color: "#a855f7" },
  { key: "gpu_server", label: "GPU server", color: "#f97316" },
  { key: "database", label: "Database", color: "#f59e0b" },
] as const

const chartData = ref<ChartItem[]>([])
const meta = ref<{ monthly_requests: number; currency: string } | null>(null)

// index-based x — the default x-scale is numeric
const x = (d: ChartItem, i: number) => i
// one y-accessor per stack segment
const y = components.map((c) => (d: ChartItem) => Number((d as any)[c.key] ?? 0))
const legendItems = computed(() =>
  components.map((c) => ({ name: c.label, color: c.color }))
)

function normalize(raw: any): ChartItem {
  return {
    model: raw?.model ?? "Unknown",
    input_cost: Number(raw?.input_cost ?? 0),
    output_cost: Number(raw?.output_cost ?? 0),
    embedding_cost: Number(raw?.embedding_cost ?? 0),
    gpu_server: Number(raw?.gpu_server ?? 0),
    database: Number(raw?.database ?? 0),
    total: Number(raw?.estimated_total ?? 0),
  }
}

onMounted(async () => {
  const response = await getStats()
  meta.value = {
    monthly_requests: response.monthly_requests,
    currency: response.currency,
  }
  chartData.value = [
    normalize(response.external_api),
    normalize(response.cost_optimized),
    normalize(response.self_hosted),
  ]
})
</script>

<template>
  <div class="w-full p-6">
    <h2 class="mb-1 text-xl font-bold">AI Infrastructure Costs</h2>
    <p v-if="meta" class="mb-4 text-sm text-muted-foreground">
      Based on {{ meta.monthly_requests.toLocaleString() }} requests/month · {{ meta.currency }}
    </p>

    <Card class="p-4">
      <VisBulletLegend :items="legendItems" class="mb-2" />

      <div style="width: 100%; height: 400px;">
        <VisXYContainer :data="chartData" :height="400">
          <VisStackedBar
            :x="x"
            :y="y"
            :color="(d: ChartItem, i: number) => components[i]?.color"
            :barPadding="0.3"
          />

          <VisAxis
            type="x"
            :tickFormat="(i: number) => chartData[i]?.model ?? ''"
          />
          <VisAxis type="y" :tickFormat="(value: number) => `$${value}`" />

          <VisTooltip />
        </VisXYContainer>
      </div>

      <!-- Totals under the chart -->
      <div class="mt-4 grid grid-cols-3 gap-4 text-center text-sm">
        <div v-for="item in chartData" :key="item.model">
          <div class="font-medium">{{ item.model }}</div>
          <div class="text-muted-foreground">${{ item.total.toFixed(2) }}/mo</div>
        </div>
      </div>
    </Card>
  </div>
</template>