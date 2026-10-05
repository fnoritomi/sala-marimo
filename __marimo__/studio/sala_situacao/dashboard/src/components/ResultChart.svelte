<script lang="ts">
  import { onMount } from "svelte";
  import * as echarts from "echarts";
  import { formatCompact, formatNumber } from "../utils/formatters";
  import { THEME_COLORS } from "../charts/echartsTheme";
  import brazilGeo from "../utils/brazilGeo.json";

  interface Props {
    columns: string[];
    rows: any[][];
    measureName?: string;
    measureLabel?: string;
    rowDimensionIds?: string[];
    colDimensionIds?: string[];
    isPivoted?: boolean;
    onApplyFilter?: (dimId: string, value: string) => void;
  }

  let {
    columns = [],
    rows = [],
    measureName = "beneficiarios",
    measureLabel = "Quantidade de Beneficiários Ativos",
    rowDimensionIds = [],
    colDimensionIds = [],
    isPivoted = false,
    onApplyFilter,
  }: Props = $props();

  type ChartType = "line" | "bar" | "area" | "pyramid" | "map" | "heatmap";

  let chartContainer: HTMLDivElement | null = $state(null);
  let chartInstance: echarts.ECharts | null = null;
  let activeChartType = $state<ChartType>("bar");
  let filterToast = $state<{ dimId: string; val: string } | null>(null);

  // Registro do mapa do Brasil (apenas uma vez)
  let mapRegistered = false;

  // Determina a sugestão automática de gráfico
  let suggestedChartType = $derived.by((): ChartType => {
    const isPyramidMatch =
      rowDimensionIds.includes("faixa_etaria") && colDimensionIds.includes("sexo");
    if (isPyramidMatch) return "pyramid";

    if (rowDimensionIds.includes("competencia")) return "line";
    if (rowDimensionIds.length === 1 && rowDimensionIds[0] === "uf") return "map";
    if (isPivoted || (rowDimensionIds.length >= 2)) return "bar";
    return "bar";
  });

  // Atualiza tipo ativo quando a sugestão mudar
  $effect(() => {
    activeChartType = suggestedChartType;
  });

  // Compatibilidade dos tipos de gráfico com a consulta
  let compatibility = $derived.by(() => {
    const hasUf = rowDimensionIds.includes("uf");
    const hasTempo = rowDimensionIds.includes("competencia");
    const isPyramid =
      rowDimensionIds.includes("faixa_etaria") && colDimensionIds.includes("sexo");
    const isMultiDim = isPivoted || rowDimensionIds.length >= 2;

    return {
      line: {
        compatible: hasTempo || isMultiDim,
        reason: "Requer dimensão temporal ou série sequencial.",
      },
      bar: {
        compatible: true,
        reason: "Compatível com qualquer combinação de dimensões.",
      },
      area: {
        compatible: hasTempo,
        reason: "Requer dimensão temporal (Competência).",
      },
      pyramid: {
        compatible: isPyramid,
        reason: "Requer 'Faixa Etária' nas Linhas e 'Sexo' nas Colunas.",
      },
      map: {
        compatible: hasUf && rowDimensionIds.length === 1,
        reason: "Requer exclusivamente 'UF' nas Linhas.",
      },
      heatmap: {
        compatible: isMultiDim,
        reason: "Requer 2 dimensões cruzadas (Linhas × Colunas).",
      },
    };
  });

  function renderChart() {
    if (!chartContainer || rows.length === 0 || columns.length === 0) return;

    if (!chartInstance) {
      chartInstance = echarts.init(chartContainer);
      chartInstance.on("click", (params: any) => {
        const clickedName = params.name || params.seriesName;
        if (clickedName && rowDimensionIds.length > 0) {
          filterToast = { dimId: rowDimensionIds[0], val: String(clickedName) };
        }
      });
    }

    if (!mapRegistered) {
      echarts.registerMap("brazil", brazilGeo as any);
      mapRegistered = true;
    }

    let option: echarts.EChartsOption = {};

    if (activeChartType === "pyramid") {
      // 1. PIRÂMIDE ETÁRIA (FAIXA ETÁRIA x SEXO)
      const faixas = rows.map((r) => String(r[0]));
      // Acha índices das colunas F e M
      const colFIdx = columns.findIndex((c) => c.toUpperCase() === "F");
      const colMIdx = columns.findIndex((c) => c.toUpperCase() === "M");

      const valsM = rows.map((r) => -(r[colMIdx] || 0)); // Valores masculinos negativos para barra esquerda
      const valsF = rows.map((r) => r[colFIdx] || 0);     // Valores femininos positivos para barra direita

      option = {
        title: {
          text: `Pirâmide Etária — ${measureLabel}`,
          subtext: "Homens (Esquerda) vs. Mulheres (Direita)",
          left: "center",
          textStyle: { fontSize: 14, fontWeight: "bold", color: "#0f172a" },
        },
        tooltip: {
          trigger: "axis",
          axisPointer: { type: "shadow" },
          formatter: (params: any) => {
            let html = `<strong>${params[0].name}</strong><br/>`;
            for (const p of params) {
              const val = Math.abs(p.value);
              html += `${p.marker} ${p.seriesName}: <strong>${formatNumber(val)}</strong><br/>`;
            }
            return html;
          },
        },
        legend: { data: ["Homens", "Mulheres"], bottom: 0 },
        grid: { left: "10%", right: "10%", top: "15%", bottom: "12%" },
        xAxis: [
          {
            type: "value",
            axisLabel: {
              formatter: (v: number) => formatCompact(Math.abs(v)),
            },
          },
        ],
        yAxis: [
          {
            type: "category",
            axisTick: { show: false },
            data: faixas,
          },
        ],
        series: [
          {
            name: "Homens",
            type: "bar",
            stack: "total",
            itemStyle: { color: "#0284c7" },
            data: valsM,
          },
          {
            name: "Mulheres",
            type: "bar",
            stack: "total",
            itemStyle: { color: "#ec4899" },
            data: valsF,
          },
        ],
      };
    } else if (activeChartType === "map") {
      // 2. MAPA DO BRASIL (UF)
      const mapData = rows.map((r) => ({
        name: String(r[0]),
        value: Number(r[r.length - 1]),
      }));
      const maxVal = Math.max(...mapData.map((d) => d.value), 1);

      option = {
        title: {
          text: `Distribuição por UF — ${measureLabel}`,
          left: "center",
          textStyle: { fontSize: 14, fontWeight: "bold", color: "#0f172a" },
        },
        tooltip: {
          trigger: "item",
          formatter: (p: any) =>
            `${p.name}: <strong>${formatNumber(p.value || 0)}</strong> beneficiários`,
        },
        visualMap: {
          min: 0,
          max: maxVal,
          left: "left",
          bottom: "bottom",
          text: ["Alto", "Baixo"],
          calculable: true,
          inRange: {
            color: ["#e0f2fe", "#0284c7", "#1e3a8a"],
          },
        },
        series: [
          {
            name: measureLabel,
            type: "map",
            map: "brazil",
            roam: true,
            emphasis: {
              label: { show: true },
              itemStyle: { areaColor: "#f59e0b" },
            },
            data: mapData,
          },
        ],
      };
    } else if (isPivoted) {
      // 3. MATRIZ PIVOT: Séries Múltiplas (Barras Agrupadas / Linhas)
      const categories = rows.map((r) => String(r[0]));
      // Colunas numéricas menos a última se for "Total"
      const seriesCols = columns.slice(1).filter((c) => c !== "Total");

      const seriesList = seriesCols.map((colName, sIdx) => {
        const colIndex = columns.indexOf(colName);
        return {
          name: colName,
          type: activeChartType === "area" ? "line" : (activeChartType as any),
          areaStyle: activeChartType === "area" ? {} : undefined,
          data: rows.map((r) => r[colIndex]),
        };
      });

      option = {
        title: {
          text: `${columns[0]} × Categorias — ${measureLabel}`,
          left: "center",
          textStyle: { fontSize: 14, fontWeight: "bold", color: "#0f172a" },
        },
        tooltip: {
          trigger: "axis",
          axisPointer: { type: "shadow" },
          valueFormatter: (v: any) => formatNumber(v),
        },
        legend: { bottom: 0, type: "scroll" },
        grid: { left: "5%", right: "5%", top: "15%", bottom: "15%", containLabel: true },
        xAxis: { type: "category", data: categories },
        yAxis: {
          type: "value",
          axisLabel: { formatter: (v: number) => formatCompact(v) },
        },
        dataZoom: categories.length > 12 ? [{ type: "inside" }, { type: "slider" }] : undefined,
        series: seriesList,
      };
    } else {
      // 4. GRÁFICO PADRÃO: 1 ou mais Dimensões em Linhas (Barras Horizontais / Linhas)
      const dimCount = Math.max(1, columns.length - 1);
      const xLabels = rows.map((r) => (dimCount > 1 ? r.slice(0, dimCount).join(" · ") : String(r[0])));
      const yValues = rows.map((r) => Number(r[r.length - 1]));
      const isHorizontal = activeChartType === "bar" && xLabels.length > 5;
      const dimLabels = columns.slice(0, dimCount).join(" × ");
      const chartTitle = `${dimLabels} — ${measureLabel}`;

      if (isHorizontal) {
        // Barras horizontais ordenadas (top 30 para legibilidade se houver muitos registros)
        const combined = xLabels.map((lbl, i) => ({ lbl, val: yValues[i] }));
        combined.sort((a, b) => a.val - b.val);
        const displayData = combined.length > 30 ? combined.slice(-30) : combined;

        option = {
          title: {
            text: chartTitle,
            subtext: combined.length > 30 ? `Exibindo maiores 30 registros de ${combined.length.toLocaleString("pt-BR")}` : undefined,
            left: "center",
            textStyle: { fontSize: 14, fontWeight: "bold", color: "#0f172a" },
            subtextStyle: { fontSize: 11, color: "#64748b" },
          },
          tooltip: {
            trigger: "axis",
            axisPointer: { type: "shadow" },
            valueFormatter: (v: any) => formatNumber(v),
          },
          grid: { left: "3%", right: "8%", top: combined.length > 30 ? "16%" : "12%", bottom: "5%", containLabel: true },
          xAxis: {
            type: "value",
            axisLabel: { formatter: (v: number) => formatCompact(v) },
          },
          yAxis: {
            type: "category",
            data: displayData.map((d) => d.lbl),
            axisLabel: { interval: 0, width: 140, overflow: "truncate" },
          },
          series: [
            {
              name: measureLabel,
              type: "bar",
              itemStyle: { color: "#2563eb", borderRadius: [0, 4, 4, 0] },
              data: displayData.map((d) => d.val),
            },
          ],
        };
      } else {
        // Linhas ou barras verticais
        option = {
          title: {
            text: chartTitle,
            left: "center",
            textStyle: { fontSize: 14, fontWeight: "bold", color: "#0f172a" },
          },
          tooltip: {
            trigger: "axis",
            valueFormatter: (v: any) => formatNumber(v),
          },
          grid: { left: "4%", right: "4%", top: "14%", bottom: "10%", containLabel: true },
          xAxis: { type: "category", data: xLabels },
          yAxis: {
            type: "value",
            axisLabel: { formatter: (v: number) => formatCompact(v) },
          },
          dataZoom: xLabels.length > 15 ? [{ type: "inside" }, { type: "slider" }] : undefined,
          series: [
            {
              name: measureLabel,
              type: (activeChartType === "area" || activeChartType === "line" ? "line" : "bar") as any,
              areaStyle: activeChartType === "area" ? { opacity: 0.25 } : undefined,
              smooth: true,
              itemStyle: { color: "#2563eb" },
              data: yValues,
            },
          ],
        };
      }
    }

    chartInstance.setOption(option, true);
  }

  $effect(() => {
    // Reexecuta sempre que mudar os dados, colunas ou o tipo de gráfico
    if (chartContainer && rows && columns && activeChartType) {
      renderChart();
    }
  });

  onMount(() => {
    renderChart();
    const handleResize = () => chartInstance?.resize();
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chartInstance?.dispose();
    };
  });
</script>

<div class="result-chart-wrapper">
  <!-- Barra de Seleção de Tipo de Gráfico -->
  <div class="chart-type-toolbar">
    <span class="toolbar-title">Tipo de Gráfico:</span>
    <div class="type-buttons">
      <button
        type="button"
        class="btn-type"
        class:active={activeChartType === "bar"}
        disabled={!compatibility.bar.compatible}
        title={compatibility.bar.reason}
        onclick={() => (activeChartType = "bar")}
      >
        📊 Barras
      </button>

      <button
        type="button"
        class="btn-type"
        class:active={activeChartType === "line"}
        disabled={!compatibility.line.compatible}
        title={compatibility.line.reason}
        onclick={() => (activeChartType = "line")}
      >
        📈 Linhas
      </button>

      <button
        type="button"
        class="btn-type"
        class:active={activeChartType === "area"}
        disabled={!compatibility.area.compatible}
        title={compatibility.area.reason}
        onclick={() => (activeChartType = "area")}
      >
        📉 Área
      </button>

      <button
        type="button"
        class="btn-type"
        class:active={activeChartType === "pyramid"}
        disabled={!compatibility.pyramid.compatible}
        title={compatibility.pyramid.reason}
        onclick={() => (activeChartType = "pyramid")}
      >
        👥 Pirâmide
      </button>

      <button
        type="button"
        class="btn-type"
        class:active={activeChartType === "map"}
        disabled={!compatibility.map.compatible}
        title={compatibility.map.reason}
        onclick={() => (activeChartType = "map")}
      >
        🗺️ Mapa Brasil
      </button>
    </div>
  </div>

  <!-- Container do Apache ECharts -->
  <div bind:this={chartContainer} class="echarts-dom-container"></div>

  <!-- Toast de Ação de Cross-Filter -->
  {#if filterToast}
    <div class="cross-filter-toast">
      <span>Selecionado: <strong>{filterToast.val}</strong></span>
      <button
        type="button"
        class="btn-apply-crossfilter"
        onclick={() => {
          if (filterToast && onApplyFilter) {
            onApplyFilter(filterToast.dimId, filterToast.val);
          }
          filterToast = null;
        }}
      >
        + Filtrar por "{filterToast.val}"
      </button>
      <button
        type="button"
        class="btn-dismiss-toast"
        onclick={() => (filterToast = null)}
      >
        ✕
      </button>
    </div>
  {/if}
</div>

<style>
  .result-chart-wrapper {
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
    position: relative;
  }

  .chart-type-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.625rem 1rem;
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .toolbar-title {
    font-size: 0.75rem;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .type-buttons {
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }

  .btn-type {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 0.25rem 0.625rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: #334155;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-type:hover:not(:disabled) {
    background: #f1f5f9;
    border-color: #94a3b8;
  }

  .btn-type.active {
    background: #1e3a8a;
    border-color: #1e3a8a;
    color: #ffffff;
  }

  .btn-type:disabled {
    opacity: 0.35;
    cursor: not-allowed;
    background: #f1f5f9;
  }

  .echarts-dom-container {
    width: 100%;
    height: 480px;
    min-height: 400px;
  }

  .cross-filter-toast {
    position: absolute;
    bottom: 1.25rem;
    left: 50%;
    transform: translateX(-50%);
    background: #0f172a;
    color: #ffffff;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.8125rem;
    z-index: 50;
    animation: fadeIn 0.2s ease;
  }

  .btn-apply-crossfilter {
    background: #2563eb;
    border: none;
    color: #ffffff;
    font-weight: 600;
    padding: 0.25rem 0.625rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.75rem;
  }

  .btn-apply-crossfilter:hover {
    background: #1d4ed8;
  }

  .btn-dismiss-toast {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 0.875rem;
    padding: 0 0.25rem;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translate(-50%, 10px); }
    to { opacity: 1; transform: translate(-50%, 0); }
  }
</style>
