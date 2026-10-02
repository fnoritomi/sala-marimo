<script lang="ts">
  import { onMount } from "svelte";
  import * as echarts from "echarts";
  import ChartCard from "./ChartCard.svelte";
  import { formatCompact, formatCurrency, formatPercent, formatCompetence } from "../utils/formatters";
  import { COMMON_CHART_OPTIONS, THEME_COLORS } from "../charts/echartsTheme";

  interface Props {
    data?: {
      competencias: string[];
      receita: number[];
      despesa_assistencial: number[];
      despesa_administrativa: number[];
      resultado_operacional: number[];
      sinistralidade: number[];
    };
  }

  let { data = { competencias: [], receita: [], despesa_assistencial: [], despesa_administrativa: [], resultado_operacional: [], sinistralidade: [] } }: Props = $props();

  let chartContainer: HTMLDivElement | null = $state(null);
  let chartInstance: echarts.ECharts | null = null;

  function updateChart() {
    if (!chartContainer || !data || data.competencias.length === 0) return;

    if (!chartInstance) {
      chartInstance = echarts.init(chartContainer);
    }

    const competencias = data.competencias.map(formatCompetence);

    const option: echarts.EChartsOption = {
      ...COMMON_CHART_OPTIONS,
      color: [THEME_COLORS.primary, THEME_COLORS.accentRed, THEME_COLORS.accentAmber],
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
            const isPercent = item.seriesName.includes("%");
            const valStr = isPercent
              ? `${Number(item.value).toFixed(1)}%`
              : formatCurrency(item.value, false);
            tip += `
              <div style="display:flex;justify-content:space-between;gap:20px;margin-bottom:4px;">
                <span>${item.marker} ${item.seriesName}</span>
                <strong style="color:#ffffff;">${valStr}</strong>
              </div>
            `;
          }
          return tip;
        },
      },
      xAxis: {
        type: "category",
        data: competencias,
        axisLine: { lineStyle: { color: THEME_COLORS.gridLine } },
        axisLabel: { color: THEME_COLORS.textMuted, fontSize: 11 },
      },
      yAxis: [
        {
          type: "value",
          name: "Valores (R$)",
          nameTextStyle: { color: THEME_COLORS.textMuted, fontSize: 11 },
          axisLine: { show: false },
          splitLine: { lineStyle: { color: THEME_COLORS.gridLine, type: "dashed" } },
          axisLabel: {
            color: THEME_COLORS.textMuted,
            formatter: (v: number) => formatCompact(v),
          },
        },
        {
          type: "value",
          name: "Sinistralidade (%)",
          nameTextStyle: { color: THEME_COLORS.textMuted, fontSize: 11 },
          min: 60,
          max: 100,
          position: "right",
          axisLine: { show: false },
          splitLine: { show: false },
          axisLabel: {
            color: THEME_COLORS.textMuted,
            formatter: (v: number) => `${v}%`,
          },
        },
      ],
      series: [
        {
          name: "Receita de Contraprestações",
          type: "bar",
          yAxisIndex: 0,
          data: data.receita,
          barMaxWidth: 16,
          itemStyle: { color: "#1e3a8a", borderRadius: [4, 4, 0, 0] },
        },
        {
          name: "Despesa Assistencial",
          type: "bar",
          yAxisIndex: 0,
          data: data.despesa_assistencial,
          barMaxWidth: 16,
          itemStyle: { color: "#f87171", borderRadius: [4, 4, 0, 0] },
        },
        {
          name: "Sinistralidade (%)",
          type: "line",
          yAxisIndex: 1,
          data: data.sinistralidade,
          smooth: true,
          symbolSize: 6,
          lineStyle: { color: "#d97706", width: 3 },
          markLine: {
            silent: true,
            symbol: "none",
            data: [
              {
                yAxis: 85,
                lineStyle: { color: "#dc2626", type: "dashed", width: 1.5 },
                label: {
                  formatter: "Referência ANS: 85%",
                  position: "insideEndTop",
                  color: "#dc2626",
                  fontSize: 10,
                },
              },
            ],
          },
        },
      ],
    };

    chartInstance.setOption(option);
  }

  $effect(() => {
    if (data && data.competencias) {
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
  title="Equilíbrio Econômico-Financeiro e Sinistralidade"
  question="Como estão se comportando as receitas e os custos assistenciais das operadoras?"
  metricId="financeiro"
>
  <div class="chart-canvas" bind:this={chartContainer}></div>
</ChartCard>

<style>
  .chart-canvas {
    width: 100%;
    height: 100%;
    min-height: 320px;
  }
</style>
