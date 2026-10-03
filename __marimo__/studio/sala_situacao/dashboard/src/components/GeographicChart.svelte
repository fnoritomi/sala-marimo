<script lang="ts">
  import { onMount } from "svelte";
  import * as echarts from "echarts";
  import ChartCard from "./ChartCard.svelte";
  import { formatCompact, formatNumber, formatPercent, downloadCsv } from "../utils/formatters";
  import { COMMON_CHART_OPTIONS, THEME_COLORS } from "../charts/echartsTheme";
  import { analyticalStore } from "../stores/analyticalStore";
  import brazilGeo from "../utils/brazilGeo.json";

  interface GeoItem {
    sigla_uf: string;
    nome_uf: string;
    regiao: string;
    populacao: number;
    vidas: number;
    taxa_cobertura: number;
  }

  interface Props {
    data?: GeoItem[];
  }

  let { data = [] }: Props = $props();

  let chartContainer: HTMLDivElement | null = $state(null);
  let chartInstance: echarts.ECharts | null = null;
  let viewMode = $state<"map" | "ranking">("map");
  let metricMode = $state<"vidas" | "cobertura">("vidas");

  function handleDownload() {
    if (!data || data.length === 0) return;
    const headers = ["sigla_uf", "nome_uf", "regiao", "populacao", "beneficiarios", "taxa_cobertura_pct"];
    const rows = data.map((d) => [
      d.sigla_uf,
      d.nome_uf,
      d.regiao,
      d.populacao,
      d.vidas,
      d.taxa_cobertura,
    ]);
    downloadCsv(`distribuicao_geografica_${new Date().toISOString().slice(0, 10)}`, headers, rows);
  }

  let mapRegistered = false;

  function updateChart() {
    if (!chartContainer || !data || data.length === 0) return;

    if (!mapRegistered) {
      echarts.registerMap("brazil", brazilGeo as any);
      mapRegistered = true;
    }

    if (!chartInstance) {
      chartInstance = echarts.init(chartContainer);
      chartInstance.on("click", (params: any) => {
        // Encontra a UF pelo nome ou sigla
        let sigla: string | null = null;
        if (params.data && params.data.sigla) {
          sigla = params.data.sigla;
        } else if (params.name) {
          const found = data.find(
            (d) => d.nome_uf.toLowerCase() === params.name.toLowerCase() || d.sigla_uf === params.name
          );
          if (found) sigla = found.sigla_uf;
        }

        if (sigla) {
          analyticalStore.toggleUf(sigla);
        }
      });
    }

    const currentUf = $analyticalStore.selectedUf;

    if (viewMode === "ranking") {
      // Ranking de barras horizontais
      const sorted = [...data].sort((a, b) => {
        const valA = metricMode === "vidas" ? a.vidas : a.taxa_cobertura;
        const valB = metricMode === "vidas" ? b.vidas : b.taxa_cobertura;
        return valA - valB;
      });

      const categories = sorted.map((d) => d.sigla_uf);
      const values = sorted.map((d) => (metricMode === "vidas" ? d.vidas : d.taxa_cobertura));

      const option: echarts.EChartsOption = {
        ...COMMON_CHART_OPTIONS,
        grid: {
          top: 10,
          left: 10,
          right: 54,
          bottom: 10,
          containLabel: true,
        },
        tooltip: {
          trigger: "axis",
          axisPointer: { type: "shadow" },
          formatter: (params: any) => {
            if (!Array.isArray(params) || params.length === 0) return "";
            const item = params[0];
            const uf = data.find((d) => d.sigla_uf === item.name);
            if (!uf) return "";
            return `
              <div style="font-weight:700;color:#f8fafc;margin-bottom:4px;">${uf.nome_uf} (${uf.sigla_uf})</div>
              <div style="color:#94a3b8;font-size:11px;margin-bottom:6px;">Região ${uf.regiao} • Pop: ${formatCompact(uf.populacao)}</div>
              <div style="color:#ffffff;">Vidas Ativas: <strong>${formatNumber(uf.vidas)}</strong></div>
              <div style="color:#38bdf8;">Taxa de Cobertura: <strong>${formatPercent(uf.taxa_cobertura)}</strong></div>
              <div style="font-size:10px;color:#94a3b8;margin-top:4px;">(Clique para cross-filter)</div>
            `;
          },
        },
        xAxis: {
          type: "value",
          axisLine: { show: false },
          splitLine: { lineStyle: { color: THEME_COLORS.gridLine, type: "dashed" } },
          axisLabel: {
            color: THEME_COLORS.textMuted,
            formatter: (v: number) => (metricMode === "vidas" ? formatCompact(v) : `${v}%`),
          },
        },
        yAxis: {
          type: "category",
          data: categories,
          axisLine: { lineStyle: { color: THEME_COLORS.gridLine } },
          axisLabel: {
            color: (val?: string | number) => (String(val) === currentUf ? "#2563eb" : THEME_COLORS.textMain),
            fontSize: 11,
          },
        },
        series: [
          {
            type: "bar",
            data: values.map((val, idx) => {
              const sigla = categories[idx];
              const isSelected = sigla === currentUf;
              return {
                value: val,
                sigla: sigla,
                itemStyle: {
                  color: isSelected
                    ? "#2563eb"
                    : metricMode === "vidas"
                    ? THEME_COLORS.primary
                    : THEME_COLORS.accentTeal,
                  borderRadius: [0, 4, 4, 0],
                },
              };
            }),
            barMaxWidth: 16,
            label: {
              show: true,
              position: "right",
              formatter: (p: any) =>
                metricMode === "vidas" ? formatCompact(p.value) : `${p.value}%`,
              color: THEME_COLORS.textMuted,
              fontSize: 10,
            },
          },
        ],
      };

      chartInstance.setOption(option, true);
    } else {
      // Mapa coroplético
      const mapData = data.map((d) => ({
        name: d.nome_uf,
        value: metricMode === "vidas" ? d.vidas : d.taxa_cobertura,
        sigla: d.sigla_uf,
        raw: d,
        selected: d.sigla_uf === currentUf,
      }));

      const maxVal = Math.max(...mapData.map((d) => d.value));

      const option: echarts.EChartsOption = {
        ...COMMON_CHART_OPTIONS,
        tooltip: {
          trigger: "item",
          formatter: (params: any) => {
            if (!params.data) return params.name;
            const uf = params.data.raw as GeoItem;
            return `
              <div style="font-weight:700;color:#f8fafc;margin-bottom:4px;">${uf.nome_uf} (${uf.sigla_uf})</div>
              <div style="color:#94a3b8;font-size:11px;margin-bottom:6px;">Região ${uf.regiao} • Pop: ${formatCompact(uf.populacao)}</div>
              <div style="color:#ffffff;">Vidas Ativas: <strong>${formatNumber(uf.vidas)}</strong></div>
              <div style="color:#38bdf8;">Taxa de Cobertura: <strong>${formatPercent(uf.taxa_cobertura)}</strong></div>
              <div style="font-size:10px;color:#94a3b8;margin-top:4px;">(Clique para cross-filter)</div>
            `;
          },
        },
        visualMap: {
          min: 0,
          max: maxVal,
          left: 16,
          bottom: 16,
          text: ["Alto", "Baixo"],
          calculable: true,
          inRange: {
            color:
              metricMode === "vidas"
                ? ["#e0f2fe", "#38bdf8", "#0284c7", "#1e3a8a"]
                : ["#ecfdf5", "#6ee7b7", "#059669", "#064e3b"],
          },
          textStyle: { color: THEME_COLORS.textMuted, fontSize: 10 },
        },
        series: [
          {
            name: "Brasil",
            type: "map",
            map: "brazil",
            roam: true,
            zoom: 1.15,
            emphasis: {
              label: { show: true, color: "#ffffff", fontWeight: "bold" },
              itemStyle: { areaColor: "#f59e0b" },
            },
            select: {
              label: { show: true, color: "#ffffff", fontWeight: "bold" },
              itemStyle: { areaColor: "#2563eb", borderColor: "#ffffff", borderWidth: 2 },
            },
            data: mapData,
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

  $effect(() => {
    // Reage quando a UF selecionada muda externamente
    const _uf = $analyticalStore.selectedUf;
    updateChart();
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
  title="Distribuição Geográfica e Cobertura"
  question="Onde os beneficiários estão concentrados e qual o nível de penetração nos estados?"
  metricId="geografia"
  onDownload={handleDownload}
>
  {#snippet actions()}
    <div class="controls-toolbar">
      <!-- Seletor de Métrica -->
      <div class="pill-group">
        <button
          type="button"
          class="btn-pill {metricMode === 'vidas' ? 'active' : ''}"
          onclick={() => {
            metricMode = "vidas";
            updateChart();
          }}
        >
          Vidas
        </button>
        <button
          type="button"
          class="btn-pill {metricMode === 'cobertura' ? 'active' : ''}"
          onclick={() => {
            metricMode = "cobertura";
            updateChart();
          }}
        >
          Cobertura %
        </button>
      </div>

      <!-- Seletor de Visão -->
      <div class="pill-group">
        <button
          type="button"
          class="btn-pill {viewMode === 'map' ? 'active' : ''}"
          onclick={() => {
            viewMode = "map";
            updateChart();
          }}
          title="Ver no mapa"
        >
          Mapa
        </button>
        <button
          type="button"
          class="btn-pill {viewMode === 'ranking' ? 'active' : ''}"
          onclick={() => {
            viewMode = "ranking";
            updateChart();
          }}
          title="Ver em ranking ordenado"
        >
          Ranking
        </button>
      </div>
    </div>
  {/snippet}

  <div class="chart-canvas" bind:this={chartContainer}></div>
</ChartCard>

<style>
  .controls-toolbar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .pill-group {
    display: flex;
    background: #f1f5f9;
    padding: 2px;
    border-radius: 6px;
    border: 1px solid #e2e8f0;
  }

  .btn-pill {
    background: none;
    border: none;
    padding: 0.25rem 0.65rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
    color: #64748b;
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-pill.active {
    background: #ffffff;
    color: #0f172a;
    font-weight: 700;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  }

  .chart-canvas {
    width: 100%;
    height: 100%;
    min-height: 380px;
  }
</style>
