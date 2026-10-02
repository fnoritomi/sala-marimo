<script lang="ts">
  import { onMount } from "svelte";
  import * as echarts from "echarts";
  import ChartCard from "./ChartCard.svelte";
  import { formatCompact, formatNumber, formatPercent } from "../utils/formatters";
  import { COMMON_CHART_OPTIONS, THEME_COLORS } from "../charts/echartsTheme";
  import { analyticalStore } from "../stores/analyticalStore";

  interface Props {
    data?: {
      competencia: string;
      contratacao: Array<{ categoria: string; vidas: number; pct: number }>;
      modalidade: Array<{ categoria: string; vidas: number; pct: number }>;
    };
  }

  let { data = { competencia: "", contratacao: [], modalidade: [] } }: Props = $props();

  let activeTab = $state<"contratacao" | "modalidade">("contratacao");
  let chartContainer: HTMLDivElement | null = $state(null);
  let chartInstance: echarts.ECharts | null = null;

  function updateChart() {
    if (!chartContainer || !data) return;

    if (!chartInstance) {
      chartInstance = echarts.init(chartContainer);
      chartInstance.on("click", (params) => {
        if (params.name) {
          if (activeTab === "contratacao") {
            analyticalStore.toggleContratacao(params.name);
          } else {
            analyticalStore.toggleModalidade(params.name);
          }
        }
      });
    }

    const currentList = activeTab === "contratacao" ? data.contratacao : data.modalidade;
    const currentSelected = activeTab === "contratacao" ? $analyticalStore.contratacao : $analyticalStore.modalidade;
    const baseColor = activeTab === "contratacao" ? THEME_COLORS.secondary : THEME_COLORS.primary;

    // Ordena de forma crescente para exibir os maiores no topo do eixo Y invertido
    const sorted = [...currentList].reverse();
    const categories = sorted.map((d) => d.categoria);
    const barData = sorted.map((d) => {
      const isSelected = d.categoria === currentSelected;
      return {
        value: d.vidas,
        itemStyle: {
          color: isSelected ? "#2563eb" : baseColor,
          borderRadius: [0, 4, 4, 0],
          borderWidth: isSelected ? 2 : 0,
          borderColor: "#1d4ed8",
        },
      };
    });

    const option: echarts.EChartsOption = {
      ...COMMON_CHART_OPTIONS,
      grid: {
        top: 20,
        left: 16,
        right: 48,
        bottom: 16,
        containLabel: true,
      },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params: any) => {
          if (!Array.isArray(params) || params.length === 0) return "";
          const item = params[0];
          const matched = currentList.find((d) => d.categoria === item.name);
          return `
            <div style="font-weight:600;margin-bottom:4px;color:#cbd5e1;">${item.name}</div>
            <div style="color:#ffffff;"><strong>${formatNumber(item.value)}</strong> vidas</div>
            <div style="color:#38bdf8;margin-top:2px;">Participação: <strong>${matched?.pct ?? 0}%</strong></div>
            <div style="font-size:10px;color:#94a3b8;margin-top:4px;">(Clique para alternar filtro)</div>
          `;
        },
      },
      xAxis: {
        type: "value",
        axisLine: { show: false },
        splitLine: { lineStyle: { color: THEME_COLORS.gridLine, type: "dashed" } },
        axisLabel: {
          color: THEME_COLORS.textMuted,
          formatter: (v: number) => formatCompact(v),
        },
      },
      yAxis: {
        type: "category",
        data: categories,
        axisLine: { lineStyle: { color: THEME_COLORS.gridLine } },
        axisLabel: {
          color: (val?: string | number) => (String(val) === currentSelected ? "#2563eb" : THEME_COLORS.textMain),
          fontSize: 11,
          width: 150,
          overflow: "truncate",
        },
      },
      series: [
        {
          type: "bar",
          data: barData,
          barMaxWidth: 26,
          label: {
            show: true,
            position: "right",
            formatter: (p: any) => {
              const matched = currentList.find((d) => d.categoria === p.name);
              return `${matched?.pct ?? 0}%`;
            },
            color: THEME_COLORS.textMuted,
            fontSize: 11,
          },
        },
      ],
    };

    chartInstance.setOption(option, true);
  }

  $effect(() => {
    const _c = $analyticalStore.contratacao;
    const _m = $analyticalStore.modalidade;
    if (data && (data.contratacao || data.modalidade)) {
      updateChart();
    }
  });

  onMount(() => {
    updateChart();
    const handleResize = () => chartInstance?.resize();
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chartInstance?.dispose();
    };
  });
</script>

<ChartCard
  title="Perfil de Vidas: Contratação e Modalidade"
  question="Como a carteira de beneficiários está distribuída por tipo de contratação e modalidade?"
  metricId="perfil"
>
  {#snippet actions()}
    <div class="tab-buttons">
      <button
        type="button"
        class="btn-tab {activeTab === 'contratacao' ? 'active' : ''}"
        onclick={() => {
          activeTab = "contratacao";
          updateChart();
        }}
      >
        Contratação
      </button>
      <button
        type="button"
        class="btn-tab {activeTab === 'modalidade' ? 'active' : ''}"
        onclick={() => {
          activeTab = "modalidade";
          updateChart();
        }}
      >
        Modalidade
      </button>
    </div>
  {/snippet}

  <div class="chart-canvas" bind:this={chartContainer}></div>
</ChartCard>

<style>
  .tab-buttons {
    display: flex;
    background: #f1f5f9;
    padding: 2px;
    border-radius: 6px;
    border: 1px solid #e2e8f0;
  }

  .btn-tab {
    background: none;
    border: none;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
    color: #64748b;
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-tab.active {
    background: #ffffff;
    color: #0f172a;
    font-weight: 700;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  }

  .chart-canvas {
    width: 100%;
    height: 100%;
    min-height: 320px;
  }
</style>
