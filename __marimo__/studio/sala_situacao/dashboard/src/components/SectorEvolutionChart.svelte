<script lang="ts">
  import { onMount } from "svelte";
  import * as echarts from "echarts";
  import ChartCard from "./ChartCard.svelte";
  import { formatCompact, formatNumber, formatCompetence, downloadCsv } from "../utils/formatters";
  import { COMMON_CHART_OPTIONS, THEME_COLORS } from "../charts/echartsTheme";

  interface Props {
    data?: {
      competencias: string[];
      medica: number[];
      odontologica: number[];
      total: number[];
    };
  }

  let { data = { competencias: [], medica: [], odontologica: [], total: [] } }: Props = $props();

  let chartContainer: HTMLDivElement | null = $state(null);
  let chartInstance: echarts.ECharts | null = null;
  let activeHorizon = $state(36); // 12, 24, 36, or 0 (all)

  function handleDownload() {
    if (!data || !data.competencias || data.competencias.length === 0) return;
    const n = data.competencias.length;
    const sliceCount = activeHorizon > 0 ? Math.min(activeHorizon, n) : n;
    const startIndex = Math.max(0, n - sliceCount);

    const comps = data.competencias.slice(startIndex);
    const med = data.medica.slice(startIndex);
    const odo = data.odontologica.slice(startIndex);
    const tot = data.total && data.total.length === n
      ? data.total.slice(startIndex)
      : med.map((v, i) => v + odo[i]);

    const headers = ["competencia", "medico_hospitalar", "exclusivamente_odontologica", "total_beneficiarios"];
    const rows = comps.map((c, i) => [c, med[i], odo[i], tot[i]]);
    const suffix = activeHorizon > 0 ? `${activeHorizon}m` : "completo";
    downloadCsv(`evolucao_beneficiarios_${suffix}_${new Date().toISOString().slice(0, 10)}`, headers, rows);
  }

  function updateChart() {
    if (!chartContainer || !data || data.competencias.length === 0) return;

    if (!chartInstance) {
      chartInstance = echarts.init(chartContainer);
    }

    const n = data.competencias.length;
    const sliceCount = activeHorizon > 0 ? Math.min(activeHorizon, n) : n;
    const startIndex = Math.max(0, n - sliceCount);

    const competencias = data.competencias.slice(startIndex).map(formatCompetence);
    const medica = data.medica.slice(startIndex);
    const odontologica = data.odontologica.slice(startIndex);

    const hasMedica = medica.some((v) => v > 0);
    const hasOdonto = odontologica.some((v) => v > 0);

    const series: any[] = [];
    const colors: string[] = [];

    if (hasMedica) {
      colors.push(THEME_COLORS.primary);
      series.push({
        name: "Médico-Hospitalar",
        type: "line",
        data: medica,
        smooth: true,
        symbolSize: 4,
        lineStyle: { width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(26, 54, 93, 0.28)" },
            { offset: 1, color: "rgba(26, 54, 93, 0.02)" },
          ]),
        },
      });
    }

    if (hasOdonto) {
      colors.push(THEME_COLORS.accentTeal);
      series.push({
        name: "Exclusivamente Odontológica",
        type: "line",
        data: odontologica,
        smooth: true,
        symbolSize: 4,
        lineStyle: { width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(13, 148, 136, 0.25)" },
            { offset: 1, color: "rgba(13, 148, 136, 0.02)" },
          ]),
        },
      });
    }

    if (series.length === 0) {
      colors.push(THEME_COLORS.primary);
      series.push({
        name: "Beneficiários",
        type: "line",
        data: data.total.slice(startIndex),
        smooth: true,
        symbolSize: 4,
        lineStyle: { width: 3 },
      });
    }

    const isMultipleSeries = series.length > 1;

    const option: echarts.EChartsOption = {
      ...COMMON_CHART_OPTIONS,
      color: colors,
      legend: {
        top: 0,
        right: 16,
        icon: "circle",
        show: isMultipleSeries,
        textStyle: { color: THEME_COLORS.textMain, fontSize: 12 },
      },
      grid: {
        top: isMultipleSeries ? 40 : 24,
        left: 16,
        right: 16,
        bottom: 56,
        containLabel: true,
      },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "line" },
        formatter: (params: any) => {
          if (!Array.isArray(params) || params.length === 0) return "";
          let tip = `<div style="font-weight:600;margin-bottom:6px;color:#cbd5e1;">Competência: ${params[0].name}</div>`;
          let sum = 0;
          for (const item of params) {
            sum += Number(item.value);
            tip += `
              <div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px;">
                <span>${item.marker} ${item.seriesName}</span>
                <strong style="color:#ffffff;">${formatNumber(item.value)} vidas</strong>
              </div>
            `;
          }
          if (isMultipleSeries) {
            tip += `<div style="border-top:1px solid #334155;margin-top:6px;padding-top:4px;display:flex;justify-content:space-between;color:#94a3b8;">
              <span>Total Consolidado</span>
              <strong style="color:#38bdf8;">${formatNumber(sum)} vidas</strong>
            </div>`;
          }
          return tip;
        },
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: competencias,
        axisLine: { lineStyle: { color: THEME_COLORS.gridLine } },
        axisLabel: { color: THEME_COLORS.textMuted, fontSize: 11 },
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        splitLine: { lineStyle: { color: THEME_COLORS.gridLine, type: "dashed" } },
        axisLabel: {
          color: THEME_COLORS.textMuted,
          formatter: (v: number) => formatCompact(v),
        },
      },
      dataZoom: [
        {
          type: "slider",
          bottom: 12,
          height: 20,
          borderColor: "transparent",
          backgroundColor: "#f1f5f9",
          fillerColor: "rgba(37, 99, 235, 0.15)",
          handleStyle: { color: "#2563eb" },
        },
      ],
      series,
    };

    chartInstance.setOption(option, true);
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
  title="Evolução Temporal de Beneficiários"
  question="Como o estoque de vidas do setor evoluiu ao longo das competências?"
  metricId="beneficiarios"
  onDownload={handleDownload}
>
  {#snippet actions()}
    <div class="horizon-buttons">
      {#each [12, 24, 36, 0] as h}
        <button
          type="button"
          class="btn-horizon {activeHorizon === h ? 'active' : ''}"
          onclick={() => {
            activeHorizon = h;
            updateChart();
          }}
        >
          {h === 0 ? "Tudo" : `${h}M`}
        </button>
      {/each}
    </div>
  {/snippet}

  <div class="chart-canvas" bind:this={chartContainer}></div>
</ChartCard>

<style>
  .horizon-buttons {
    display: flex;
    background: #f1f5f9;
    padding: 2px;
    border-radius: 6px;
    border: 1px solid #e2e8f0;
  }

  .btn-horizon {
    background: none;
    border: none;
    padding: 0.25rem 0.6rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
    color: #64748b;
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-horizon.active {
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
