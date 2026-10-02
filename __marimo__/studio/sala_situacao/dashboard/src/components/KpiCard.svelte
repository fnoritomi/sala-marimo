<script lang="ts">
  import { onMount } from "svelte";
  import * as echarts from "echarts";
  import { analyticalStore } from "../stores/analyticalStore";

  interface Props {
    title: string;
    value: string;
    subtitle?: string;
    delta?: number;
    deltaText?: string;
    sparklineData?: number[];
    metricId: string;
    invertDeltaColors?: boolean; // Para sinistralidade ou reclamações, onde subida é alerta
  }

  let {
    title,
    value,
    subtitle = "em 12 meses",
    delta,
    deltaText,
    sparklineData = [],
    metricId,
    invertDeltaColors = false,
  }: Props = $props();

  let sparkContainer: HTMLDivElement | null = $state(null);
  let chartInstance: echarts.ECharts | null = null;

  $effect(() => {
    if (sparkContainer && sparklineData && sparklineData.length > 1) {
      if (!chartInstance) {
        chartInstance = echarts.init(sparkContainer, null, { renderer: "svg" });
      }

      const isPositive = (delta ?? 0) >= 0;
      const lineColor = invertDeltaColors
        ? (isPositive ? "#dc2626" : "#16a34a")
        : (isPositive ? "#16a34a" : "#dc2626");

      chartInstance.setOption({
        grid: { left: 0, right: 0, top: 2, bottom: 2 },
        xAxis: { type: "category", show: false },
        yAxis: { type: "value", show: false, min: "dataMin" },
        series: [
          {
            type: "line",
            data: sparklineData,
            smooth: true,
            symbol: "none",
            lineStyle: { color: lineColor, width: 2 },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: `${lineColor}44` },
                { offset: 1, color: `${lineColor}05` },
              ]),
            },
          },
        ],
      });
    }
  });

  onMount(() => {
    return () => {
      chartInstance?.dispose();
    };
  });
</script>

<div class="kpi-card">
  <div class="kpi-header">
    <span class="kpi-title">{title}</span>
    <button
      type="button"
      class="btn-info"
      onclick={() => analyticalStore.openMetadata(metricId)}
      title="Ver detalhes metodológicos"
    >
      ⓘ
    </button>
  </div>

  <div class="kpi-body">
    <div class="kpi-value-block">
      <span class="kpi-main-value">{value}</span>
      
      {#if delta !== undefined}
        {@const isUp = delta >= 0}
        {@const isGood = invertDeltaColors ? !isUp : isUp}
        <div class="kpi-delta {isGood ? 'delta-good' : 'delta-bad'}">
          <span class="delta-arrow">{isUp ? "▲" : "▼"}</span>
          <span>{deltaText ?? `${Math.abs(delta).toFixed(1)}%`}</span>
          <span class="delta-period">{subtitle}</span>
        </div>
      {/if}
    </div>

    {#if sparklineData && sparklineData.length > 1}
      <div class="sparkline-wrapper" bind:this={sparkContainer}></div>
    {/if}
  </div>
</div>

<style>
  .kpi-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1.15rem 1.25rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }

  .kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  .kpi-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .kpi-title {
    font-size: 0.8125rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #64748b;
  }

  .btn-info {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 0.875rem;
    padding: 0.1rem 0.3rem;
    border-radius: 4px;
    line-height: 1;
    transition: color 0.15s;
  }

  .btn-info:hover {
    color: #2563eb;
    background: #eff6ff;
  }

  .kpi-body {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 0.75rem;
  }

  .kpi-value-block {
    display: flex;
    flex-direction: column;
  }

  .kpi-main-value {
    font-size: 1.875rem;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.03em;
    line-height: 1.1;
  }

  .kpi-delta {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.75rem;
    font-weight: 600;
    margin-top: 0.35rem;
  }

  .delta-good {
    color: #16a34a;
  }

  .delta-bad {
    color: #dc2626;
  }

  .delta-arrow {
    font-size: 0.65rem;
  }

  .delta-period {
    color: #94a3b8;
    font-weight: 400;
    margin-left: 0.2rem;
  }

  .sparkline-wrapper {
    width: 90px;
    height: 38px;
    flex-shrink: 0;
  }
</style>
