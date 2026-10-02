<script lang="ts">
  import { onMount } from "svelte";
  import * as echarts from "echarts";
  import ChartCard from "./ChartCard.svelte";
  import { formatCompact, formatNumber, formatPercent, formatCompetence } from "../utils/formatters";
  import { COMMON_CHART_OPTIONS, THEME_COLORS } from "../charts/echartsTheme";

  interface Props {
    data?: {
      serie_temporal: {
        competencias: string[];
        total: number[];
        resolvidas: number[];
        taxa_resolucao: number[];
      };
      temas: Array<{
        tema: string;
        natureza: string;
        total: number;
      }>;
    };
  }

  let { data = { serie_temporal: { competencias: [], total: [], resolvidas: [], taxa_resolucao: [] }, temas: [] } }: Props = $props();

  let chartContainer: HTMLDivElement | null = $state(null);
  let chartInstance: echarts.ECharts | null = null;
  let activeTab = $state<"evolucao" | "temas">("evolucao");

  function updateChart() {
    if (!chartContainer || !data) return;

    if (!chartInstance) {
      chartInstance = echarts.init(chartContainer);
    }

    if (activeTab === "evolucao") {
      const { competencias, total, resolvidas, taxa_resolucao } = data.serie_temporal;
      const formattedComps = competencias.map(formatCompetence);

      const option: echarts.EChartsOption = {
        ...COMMON_CHART_OPTIONS,
        color: [THEME_COLORS.primary, THEME_COLORS.accentGreen, THEME_COLORS.secondary],
        legend: {
          top: 0,
          right: 16,
          icon: "circle",
          textStyle: { color: THEME_COLORS.textMain, fontSize: 12 },
        },
        grid: {
          top: 40,
          left: 16,
          right: 48,
          bottom: 24,
          containLabel: true,
        },
        tooltip: {
          trigger: "axis",
          axisPointer: { type: "cross" },
          formatter: (params: any) => {
            if (!Array.isArray(params) || params.length === 0) return "";
            let tip = `<div style="font-weight:700;margin-bottom:6px;color:#cbd5e1;">Competência: ${params[0].name}</div>`;
            for (const item of params) {
              const isPct = item.seriesName.includes("%");
              tip += `
                <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px;">
                  <span>${item.marker} ${item.seriesName}</span>
                  <strong style="color:#ffffff;">${isPct ? `${item.value}%` : formatNumber(item.value)}</strong>
                </div>
              `;
            }
            return tip;
          },
        },
        xAxis: {
          type: "category",
          data: formattedComps,
          axisLine: { lineStyle: { color: THEME_COLORS.gridLine } },
          axisLabel: { color: THEME_COLORS.textMuted, fontSize: 11 },
        },
        yAxis: [
          {
            type: "value",
            name: "Demandas NIP",
            nameTextStyle: { color: THEME_COLORS.textMuted, fontSize: 11 },
            axisLine: { show: false },
            splitLine: { lineStyle: { color: THEME_COLORS.gridLine, type: "dashed" } },
            axisLabel: { color: THEME_COLORS.textMuted, formatter: (v: number) => formatCompact(v) },
          },
          {
            type: "value",
            name: "Resolutividade (%)",
            min: 60,
            max: 100,
            position: "right",
            axisLine: { show: false },
            splitLine: { show: false },
            axisLabel: { color: THEME_COLORS.textMuted, formatter: (v: number) => `${v}%` },
          },
        ],
        series: [
          {
            name: "Total de Demandas",
            type: "bar",
            yAxisIndex: 0,
            data: total,
            barMaxWidth: 16,
            itemStyle: { color: "#334155", borderRadius: [4, 4, 0, 0] },
          },
          {
            name: "Demandas Resolvidas (NIP)",
            type: "bar",
            yAxisIndex: 0,
            data: resolvidas,
            barMaxWidth: 16,
            itemStyle: { color: "#10b981", borderRadius: [4, 4, 0, 0] },
          },
          {
            name: "Resolutividade (%)",
            type: "line",
            yAxisIndex: 1,
            data: taxa_resolucao,
            smooth: true,
            symbolSize: 6,
            lineStyle: { color: "#2563eb", width: 3 },
          },
        ],
      };

      chartInstance.setOption(option, true);
    } else {
      // Decomposição por temas
      const sorted = [...data.temas].reverse();
      const categories = sorted.map((d) => d.tema);
      const values = sorted.map((d) => d.total);

      const option: echarts.EChartsOption = {
        ...COMMON_CHART_OPTIONS,
        grid: {
          top: 10,
          left: 16,
          right: 54,
          bottom: 16,
          containLabel: true,
        },
        tooltip: {
          trigger: "axis",
          axisPointer: { type: "shadow" },
          formatter: (params: any) => {
            if (!Array.isArray(params) || params.length === 0) return "";
            const item = params[0];
            const found = data.temas.find((t) => t.tema === item.name);
            return `
              <div style="font-weight:700;color:#f8fafc;margin-bottom:4px;">${item.name}</div>
              <div style="color:#94a3b8;font-size:11px;margin-bottom:4px;">Natureza: ${found?.natureza}</div>
              <div style="color:#ffffff;">Demandas: <strong>${formatNumber(item.value)}</strong></div>
            `;
          },
        },
        xAxis: {
          type: "value",
          axisLine: { show: false },
          splitLine: { lineStyle: { color: THEME_COLORS.gridLine, type: "dashed" } },
          axisLabel: { color: THEME_COLORS.textMuted, formatter: (v: number) => formatCompact(v) },
        },
        yAxis: {
          type: "category",
          data: categories,
          axisLine: { lineStyle: { color: THEME_COLORS.gridLine } },
          axisLabel: {
            color: THEME_COLORS.textMain,
            fontSize: 11,
            width: 170,
            overflow: "truncate",
          },
        },
        series: [
          {
            type: "bar",
            data: values.map((val, idx) => {
              const item = sorted[idx];
              return {
                value: val,
                itemStyle: {
                  color: item.natureza === "Assistencial" ? "#dc2626" : "#2563eb",
                  borderRadius: [0, 4, 4, 0],
                },
              };
            }),
            barMaxWidth: 20,
            label: {
              show: true,
              position: "right",
              formatter: (p: any) => formatCompact(p.value),
              color: THEME_COLORS.textMuted,
              fontSize: 10,
            },
          },
        ],
      };

      chartInstance.setOption(option, true);
    }
  }

  $effect(() => {
    if (data) {
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
  title="Demandas de Consumidores (NIP)"
  question="Qual é o volume de reclamações e a eficácia da resolução preliminar de conflitos?"
  metricId="demandas"
>
  {#snippet actions()}
    <div class="tab-buttons">
      <button
        type="button"
        class="btn-tab {activeTab === 'evolucao' ? 'active' : ''}"
        onclick={() => {
          activeTab = "evolucao";
          updateChart();
        }}
      >
        Evolução e Resolução
      </button>
      <button
        type="button"
        class="btn-tab {activeTab === 'temas' ? 'active' : ''}"
        onclick={() => {
          activeTab = "temas";
          updateChart();
        }}
      >
        Temas Reclamados
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
