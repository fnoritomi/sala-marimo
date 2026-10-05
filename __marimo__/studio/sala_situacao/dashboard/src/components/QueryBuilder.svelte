<script lang="ts">
  import MeasurePicker from "./MeasurePicker.svelte";
  import DimensionPicker from "./DimensionPicker.svelte";
  import FilterBuilder from "./FilterBuilder.svelte";
  import PivotTable from "./PivotTable.svelte";
  import ResultChart from "./ResultChart.svelte";
  import QueryDefinitions from "./QueryDefinitions.svelte";

  interface Dimension {
    id: string;
    group: string;
    label: string;
    type: string;
    cardinality: number;
    values?: any[];
  }

  interface Measure {
    id: string;
    label: string;
    type: string;
    aggregation: string;
    is_semi_additive: boolean;
    description: string;
    format: string;
  }

  interface Group {
    id: string;
    label: string;
    icon?: string;
  }

  interface Template {
    id: string;
    title: string;
    description: string;
    measure: string;
    rows: string[];
    columns: string[];
    filters: any[];
    suggested_chart: string;
  }

  interface FrontendSpec {
    dataset: any;
    measures: Measure[];
    dimension_groups: Group[];
    dimensions: Dimension[];
    templates: Template[];
  }

  interface QueryResultData {
    columns: string[];
    rows: any[][];
    total_rows: number;
    estimated_groups: number;
    query_ms: number;
    sql: string;
    semi_additive_applied: boolean;
    effective_competencia: string | null;
    measure_name: string;
    measure_label: string;
    is_pivoted: boolean;
    warning?: string | null;
    error?: string | null;
  }

  interface Props {
    spec?: FrontendSpec | null;
    result?: QueryResultData | null;
    isLoading?: boolean;
    onExecuteQuery: (queryObj: any) => void;
  }

  let { spec = null, result = null, isLoading = false, onExecuteQuery }: Props = $props();

  // Estado do Construtor de Consulta
  let activeMeasure = $state<string>("beneficiarios");
  let selectedRows = $state<string[]>(["competencia"]);
  let selectedColumns = $state<string[]>([]);
  let activeFilters = $state<any[]>([]);

  // Aba ativa de resultado: 'table' | 'chart' | 'definitions' | 'sql'
  let activeResultTab = $state<"table" | "chart" | "definitions" | "sql">("table");

  // Controle de modal do DimensionPicker
  let pickerTarget = $state<"rows" | "columns" | null>(null);

  // Dimensões e grupos fornecidos pelo spec (com fallback)
  let dimensionsList = $derived(spec?.dimensions || []);
  let groupsList = $derived(spec?.dimension_groups || []);
  let measuresList = $derived(spec?.measures || []);
  let templatesList = $derived(spec?.templates || []);

  function getDimLabel(dimId: string): string {
    const d = dimensionsList.find((item) => item.id === dimId);
    return d ? d.label : dimId;
  }

  function handleSelectDimension(dimId: string) {
    if (pickerTarget === "rows") {
      if (!selectedRows.includes(dimId)) {
        selectedRows = [...selectedRows, dimId];
      }
    } else if (pickerTarget === "columns") {
      if (!selectedColumns.includes(dimId)) {
        // Pivot suporta 1 dimensão nas colunas
        selectedColumns = [dimId];
      }
    }
    pickerTarget = null;
  }

  function removeRowDimension(dimId: string) {
    selectedRows = selectedRows.filter((id) => id !== dimId);
  }

  function removeColDimension(dimId: string) {
    selectedColumns = selectedColumns.filter((id) => id !== dimId);
  }

  function moveRowDimension(index: number, direction: "up" | "down") {
    const targetIdx = direction === "up" ? index - 1 : index + 1;
    if (targetIdx < 0 || targetIdx >= selectedRows.length) return;
    const item = selectedRows[index];
    const newArr = [...selectedRows];
    newArr.splice(index, 1);
    newArr.splice(targetIdx, 0, item);
    selectedRows = newArr;
  }

  function applyTemplate(tpl: Template) {
    activeMeasure = tpl.measure;
    selectedRows = [...tpl.rows];
    selectedColumns = [...tpl.columns];
    activeFilters = [...tpl.filters];
    activeResultTab = tpl.suggested_chart === "line" || tpl.suggested_chart === "pyramid" || tpl.suggested_chart === "map"
      ? "chart"
      : "table";
    triggerExecution();
  }

  function triggerExecution() {
    const queryObj = {
      measure: activeMeasure,
      rows: selectedRows,
      columns: selectedColumns,
      filters: activeFilters,
      limit: 10000,
    };
    onExecuteQuery(queryObj);
  }

  function handleApplyCrossFilter(dimId: string, val: string) {
    // Adiciona valor como filtro e reexecuta
    const existing = activeFilters.find((f) => f.dimension === dimId);
    if (existing) {
      if (!existing.values.includes(val)) {
        existing.values.push(val);
      }
    } else {
      activeFilters.push({
        dimension: dimId,
        operator: "in",
        values: [val],
      });
    }
    activeFilters = [...activeFilters];
    triggerExecution();
  }

  function resetQuery() {
    activeMeasure = "beneficiarios";
    selectedRows = ["competencia"];
    selectedColumns = [];
    activeFilters = [];
    triggerExecution();
  }
</script>

<div class="query-builder-root">
  <!-- Banner Informativo -->
  <div class="intro-banner">
    <div class="banner-text">
      <h2 class="title">Explorar Beneficiários — Consulta Multidimensional</h2>
      <p class="desc">
        Construtor analítico de alta performance inspirado no <strong>Caderno 2.0 da ANS</strong>.
        Cruze estoques mensais, adesões e cancelamentos com pushdown vetorial direto sobre 81,2M de registros.
      </p>
    </div>

    <!-- Barra de Templates / Atalhos Rápidos -->
    <div class="templates-bar">
      <span class="templates-label">Consultas Rápidas:</span>
      <div class="templates-chips">
        {#each templatesList as tpl}
          <button
            type="button"
            class="btn-template"
            onclick={() => applyTemplate(tpl)}
            title={tpl.description}
          >
            {tpl.title}
          </button>
        {/each}
      </div>
    </div>
  </div>

  <!-- Painel do Construtor de Consulta -->
  <section class="builder-control-panel">
    <!-- 1. SELETOR DE MEDIDA -->
    <MeasurePicker
      measures={measuresList}
      selectedMeasure={activeMeasure}
      onChange={(mId) => (activeMeasure = mId)}
    />

    <!-- 2. LINHAS, COLUNAS E FILTROS -->
    <div class="builder-axes-grid">
      <!-- Eixo de Linhas -->
      <div class="axis-box">
        <div class="axis-header">
          <span class="axis-name">LINHAS (Agrupamento Principal)</span>
          <span class="axis-sub">Dimensões exibidas nas linhas da tabela</span>
        </div>
        <div class="chips-container">
          {#if selectedRows.length === 0}
            <span class="empty-axis-text">Nenhuma dimensão selecionada (Total Geral).</span>
          {:else}
            {#each selectedRows as dimId, idx}
              <div class="dim-chip">
                {#if idx > 0}
                  <button type="button" class="btn-arrow" onclick={() => moveRowDimension(idx, "up")} title="Mover para esquerda">◀</button>
                {/if}
                <span class="chip-text">{getDimLabel(dimId)}</span>
                {#if idx < selectedRows.length - 1}
                  <button type="button" class="btn-arrow" onclick={() => moveRowDimension(idx, "down")} title="Mover para direita">▶</button>
                {/if}
                <button type="button" class="btn-remove-chip" onclick={() => removeRowDimension(dimId)} title="Remover dimensão">✕</button>
              </div>
            {/each}
          {/if}
          <button
            type="button"
            class="btn-add-axis-dim"
            onclick={() => (pickerTarget = "rows")}
          >
            + Adicionar dimensão
          </button>
        </div>
      </div>

      <!-- Eixo de Colunas (Pivot) -->
      <div class="axis-box">
        <div class="axis-header">
          <span class="axis-name">COLUNAS (Pivot Matricial)</span>
          <span class="axis-sub">Transpõe uma dimensão para as colunas da tabela</span>
        </div>
        <div class="chips-container">
          {#if selectedColumns.length === 0}
            <span class="empty-axis-text">Nenhuma dimensão em colunas (Tabela Plana).</span>
          {:else}
            {#each selectedColumns as dimId}
              <div class="dim-chip chip-pivot">
                <span class="chip-text">{getDimLabel(dimId)}</span>
                <button type="button" class="btn-remove-chip" onclick={() => removeColDimension(dimId)} title="Remover dimensão de coluna">✕</button>
              </div>
            {/each}
          {/if}
          {#if selectedColumns.length === 0}
            <button
              type="button"
              class="btn-add-axis-dim"
              onclick={() => (pickerTarget = "columns")}
            >
              + Adicionar dimensão às colunas
            </button>
          {/if}
        </div>
      </div>
    </div>

    <!-- 3. FILTROS -->
    <div class="filters-panel">
      <div class="axis-header">
        <span class="axis-name">FILTROS ANALÍTICOS</span>
        <span class="axis-sub">Restrinja o escopo da consulta por qualquer dimensão</span>
      </div>
      <FilterBuilder
        dimensions={dimensionsList}
        filters={activeFilters}
        onFiltersChange={(f) => (activeFilters = f)}
      />
    </div>

    <!-- Barra de Execução de Consulta -->
    <div class="action-footer">
      <div class="action-stats">
        {#if result && !isLoading}
          <span class="stat-badge">Tempo DuckDB: <strong>{result.query_ms} ms</strong></span>
          <span class="stat-badge">Registros: <strong>{result.total_rows.toLocaleString("pt-BR")}</strong></span>
          {#if result.semi_additive_applied}
            <span class="stat-badge badge-snapshot" title="Regra semi-aditiva aplicada automaticamente">
              Snapshot: <strong>{result.effective_competencia}</strong>
            </span>
          {/if}
        {/if}
      </div>

      <div class="buttons-right">
        <button type="button" class="btn-reset" onclick={resetQuery} title="Voltar à consulta padrão">
          Restaurar Padrão
        </button>
        <button
          type="button"
          class="btn-execute"
          disabled={isLoading}
          onclick={triggerExecution}
        >
          {#if isLoading}
            <span class="spinner"></span> Executando DuckDB...
          {:else}
            ⚡ Executar Consulta
          {/if}
        </button>
      </div>
    </div>

    <!-- Alertas e Avisos -->
    {#if result?.warning}
      <div class="warning-banner">
        ⚠️ <strong>Atenção:</strong> {result.warning}
      </div>
    {/if}
    {#if result?.error}
      <div class="error-banner">
        ❌ <strong>Erro:</strong> {result.error}
      </div>
    {/if}
  </section>

  <!-- Seção de Resultados -->
  <section class="results-section">
    <!-- Abas de Visualização do Resultado -->
    <div class="result-tabs-nav">
      <div class="tabs-group">
        <button
          type="button"
          class="tab-btn"
          class:active={activeResultTab === "table"}
          onclick={() => (activeResultTab = "table")}
        >
          📋 Resultado Tabular
        </button>
        <button
          type="button"
          class="tab-btn"
          class:active={activeResultTab === "chart"}
          onclick={() => (activeResultTab = "chart")}
        >
          📊 Gráficos & Visualização
        </button>
        <button
          type="button"
          class="tab-btn"
          class:active={activeResultTab === "definitions"}
          onclick={() => (activeResultTab = "definitions")}
        >
          ℹ Definições Metodológicas
        </button>
        <button
          type="button"
          class="tab-btn"
          class:active={activeResultTab === "sql"}
          onclick={() => (activeResultTab = "sql")}
        >
          🔍 Ver SQL Parametrizado
        </button>
      </div>
    </div>

    <!-- Conteúdo da Aba Ativa -->
    <div class="tab-content-area">
      {#if isLoading}
        <div class="loading-placeholder">
          <div class="large-spinner"></div>
          <p>Consultando Parquet remoto via DuckDB HTTPS...</p>
          <span class="loading-sub">Executando pushdown de predicados e agrupamento analítico</span>
        </div>
      {:else if result && result.rows.length >= 0}
        {#if activeResultTab === "table"}
          <PivotTable
            columns={result.columns}
            rows={result.rows}
            measureName={result.measure_name}
            isPivoted={result.is_pivoted}
            semiAdditiveApplied={result.semi_additive_applied}
          />
        {:else if activeResultTab === "chart"}
          <ResultChart
            columns={result.columns}
            rows={result.rows}
            measureName={result.measure_name}
            measureLabel={result.measure_label}
            rowDimensionIds={selectedRows}
            colDimensionIds={selectedColumns}
            isPivoted={result.is_pivoted}
            onApplyFilter={handleApplyCrossFilter}
          />
        {:else if activeResultTab === "definitions" || activeResultTab === "sql"}
          <QueryDefinitions
            measureName={result.measure_name}
            measureLabel={result.measure_label}
            rowDimensionLabels={selectedRows.map((id) => getDimLabel(id))}
            colDimensionLabels={selectedColumns.map((id) => getDimLabel(id))}
            filters={activeFilters}
            semiAdditiveApplied={result.semi_additive_applied}
            effectiveCompetencia={result.effective_competencia}
            sql={result.sql}
          />
        {/if}
      {:else}
        <div class="empty-results-box">
          <p>Clique em <strong>Executar Consulta</strong> para processar os dados.</p>
        </div>
      {/if}
    </div>
  </section>
</div>

<!-- Modal DimensionPicker -->
{#if pickerTarget}
  <DimensionPicker
    title={pickerTarget === "rows" ? "Adicionar Dimensão às Linhas" : "Adicionar Dimensão às Colunas (Pivot)"}
    dimensions={dimensionsList}
    groups={groupsList}
    selectedIds={pickerTarget === "rows" ? selectedRows : selectedColumns}
    onSelect={handleSelectDimension}
    onClose={() => (pickerTarget = null)}
  />
{/if}

<style>
  .query-builder-root {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    width: 100%;
  }

  .intro-banner {
    background: #ffffff;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    padding: 1.25rem 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .title {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 800;
    color: #0f172a;
  }

  .desc {
    margin: 0.25rem 0 0 0;
    font-size: 0.875rem;
    color: #475569;
    line-height: 1.4;
  }

  .templates-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid #f1f5f9;
    flex-wrap: wrap;
  }

  .templates-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
  }

  .templates-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .btn-template {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 6px;
    padding: 0.3rem 0.625rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: #1e40af;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-template:hover {
    background: #dbeafe;
    border-color: #93c5fd;
    transform: translateY(-1px);
  }

  .builder-control-panel {
    background: #ffffff;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    padding: 1.25rem 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .builder-axes-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.25rem;
  }

  @media (max-width: 900px) {
    .builder-axes-grid {
      grid-template-columns: 1fr;
    }
  }

  .axis-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.875rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .axis-header {
    display: flex;
    flex-direction: column;
  }

  .axis-name {
    font-size: 0.75rem;
    font-weight: 700;
    color: #334155;
    letter-spacing: 0.05em;
  }

  .axis-sub {
    font-size: 0.6875rem;
    color: #64748b;
  }

  .chips-container {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    min-height: 38px;
  }

  .empty-axis-text {
    font-size: 0.75rem;
    color: #94a3b8;
    font-style: italic;
  }

  .dim-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 0.25rem 0.5rem;
    font-size: 0.8125rem;
    font-weight: 600;
    color: #1e293b;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  }

  .chip-pivot {
    border-color: #818cf8;
    background: #eef2ff;
    color: #3730a3;
  }

  .btn-arrow, .btn-remove-chip {
    background: none;
    border: none;
    padding: 0 0.15rem;
    color: #94a3b8;
    cursor: pointer;
    font-size: 0.75rem;
    line-height: 1;
  }

  .btn-arrow:hover { color: #2563eb; }
  .btn-remove-chip:hover { color: #ef4444; }

  .btn-add-axis-dim {
    background: #ffffff;
    border: 1px dashed #cbd5e1;
    border-radius: 6px;
    padding: 0.25rem 0.625rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: #475569;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-add-axis-dim:hover {
    border-color: #2563eb;
    color: #2563eb;
    background: #f8faff;
  }

  .filters-panel {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.875rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .action-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 0.75rem;
    border-top: 1px solid #f1f5f9;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .action-stats {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .stat-badge {
    background: #f1f5f9;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    color: #475569;
  }

  .badge-snapshot {
    background: #fef3c7;
    color: #92400e;
  }

  .buttons-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .btn-reset {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 0.5rem 0.875rem;
    font-size: 0.8125rem;
    font-weight: 500;
    color: #64748b;
    cursor: pointer;
  }

  .btn-reset:hover {
    background: #f1f5f9;
    color: #0f172a;
  }

  .btn-execute {
    background: #1e3a8a;
    border: 1px solid #1e40af;
    border-radius: 6px;
    padding: 0.55rem 1.25rem;
    font-size: 0.875rem;
    font-weight: 700;
    color: #ffffff;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(30, 58, 138, 0.2);
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    transition: all 0.15s ease;
  }

  .btn-execute:hover:not(:disabled) {
    background: #1d4ed8;
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(30, 58, 138, 0.25);
  }

  .btn-execute:disabled {
    opacity: 0.7;
    cursor: wait;
  }

  .spinner {
    width: 0.875rem;
    height: 0.875rem;
    border: 2px solid rgba(255, 255, 255, 0.4);
    border-top-color: #ffffff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  .warning-banner {
    background: #fffbeb;
    border: 1px solid #fde68a;
    color: #92400e;
    padding: 0.625rem 1rem;
    border-radius: 6px;
    font-size: 0.8125rem;
  }

  .error-banner {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #991b1b;
    padding: 0.625rem 1rem;
    border-radius: 6px;
    font-size: 0.8125rem;
  }

  /* Seção de Resultados */
  .results-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .result-tabs-nav {
    display: flex;
    border-bottom: 2px solid #e2e8f0;
  }

  .tabs-group {
    display: flex;
    gap: 0.25rem;
  }

  .tab-btn {
    background: none;
    border: none;
    padding: 0.625rem 1rem;
    font-size: 0.875rem;
    font-weight: 600;
    color: #64748b;
    cursor: pointer;
    border-bottom: 3px solid transparent;
    margin-bottom: -2px;
    transition: all 0.15s ease;
  }

  .tab-btn:hover {
    color: #0f172a;
  }

  .tab-btn.active {
    color: #1e3a8a;
    border-bottom-color: #1e3a8a;
    font-weight: 700;
  }

  .tab-content-area {
    min-height: 380px;
  }

  .loading-placeholder {
    background: #ffffff;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    padding: 4rem 1rem;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    color: #1e293b;
  }

  .large-spinner {
    width: 2.5rem;
    height: 2.5rem;
    border: 3px solid #e2e8f0;
    border-top-color: #1e3a8a;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  .loading-sub {
    font-size: 0.75rem;
    color: #64748b;
  }

  .empty-results-box {
    background: #ffffff;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    padding: 3rem 1rem;
    text-align: center;
    color: #64748b;
    font-size: 0.875rem;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
</style>
