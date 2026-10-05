<script lang="ts">
  interface FilterSpec {
    dimension: string;
    operator: string;
    values: any[];
  }

  interface Props {
    measureName?: string;
    measureLabel?: string;
    rowDimensionLabels?: string[];
    colDimensionLabels?: string[];
    filters?: FilterSpec[];
    semiAdditiveApplied?: boolean;
    effectiveCompetencia?: string | null;
    sql?: string;
  }

  let {
    measureName = "beneficiarios",
    measureLabel = "Quantidade de Beneficiários Ativos",
    rowDimensionLabels = [],
    colDimensionLabels = [],
    filters = [],
    semiAdditiveApplied = false,
    effectiveCompetencia = null,
    sql = "",
  }: Props = $props();

  let copiedSql = $state(false);

  function copySqlToClipboard() {
    if (!sql) return;
    navigator.clipboard?.writeText(sql);
    copiedSql = true;
    setTimeout(() => (copiedSql = false), 2000);
  }
</script>

<div class="definitions-container">
  <div class="definitions-grid">
    <!-- Card 1: Medida e Agregação -->
    <div class="def-card">
      <h4 class="card-title">Métrica Analítica</h4>
      <div class="card-content">
        <p class="field-item">
          <span class="lbl">Medida:</span>
          <strong>{measureLabel}</strong>
        </p>
        <p class="field-item">
          <span class="lbl">Agregação:</span>
          <code>SUM({measureName === "beneficiarios" ? "QT_ATIVOS" : measureName === "adesoes" ? "QT_ADESOES" : "QT_CANCELAMENTOS"})</code>
        </p>
        <p class="field-item">
          <span class="lbl">Comportamento Temporal:</span>
          {#if measureName === "beneficiarios"}
            <span class="badge badge-semi">Medida de Estoque (Semi-Aditiva)</span>
          {:else}
            <span class="badge badge-additive">Medida de Fluxo (Aditiva)</span>
          {/if}
        </p>
      </div>
    </div>

    <!-- Card 2: Regra de Semi-Aditividade -->
    <div class="def-card">
      <h4 class="card-title">Regra Metodológica de Estoque</h4>
      <div class="card-content">
        {#if measureName === "beneficiarios"}
          {#if semiAdditiveApplied}
            <div class="alert-box alert-applied">
              <span class="alert-icon">✓</span>
              <div>
                <strong>Regra Semi-Aditiva Aplicada:</strong>
                <p>Como a dimensão temporal não foi colocada nas linhas/colunas, os dados foram automaticamente limitados ao último snapshot mensal disponível (<strong>{effectiveCompetencia || "2022-12-01"}</strong>) para evitar duplicação indevida de vidas.</p>
              </div>
            </div>
          {:else}
            <div class="alert-box alert-grouped">
              <span class="alert-icon">ℹ</span>
              <div>
                <strong>Agrupamento Temporal Ativo:</strong>
                <p>A dimensão "Mês Competência" está presente no agrupamento. Cada linha representa o snapshot real do respectivo mês.</p>
              </div>
            </div>
          {/if}
        {:else}
          <p class="field-item">
            Esta métrica representa um <strong>fluxo contínuo de eventos mensais</strong> e pode ser livremente somada entre diferentes competências.
          </p>
        {/if}
      </div>
    </div>

    <!-- Card 3: Estrutura Multidimensional -->
    <div class="def-card">
      <h4 class="card-title">Dimensões & Filtros</h4>
      <div class="card-content">
        <p class="field-item">
          <span class="lbl">Linhas (Agrupamento Principal):</span>
          <span>{rowDimensionLabels.length > 0 ? rowDimensionLabels.join(", ") : "Nenhuma (Total Geral)"}</span>
        </p>
        <p class="field-item">
          <span class="lbl">Colunas (Pivot Matricial):</span>
          <span>{colDimensionLabels.length > 0 ? colDimensionLabels.join(", ") : "Nenhuma (Formato Tabela Plana)"}</span>
        </p>
        <div class="field-item">
          <span class="lbl">Filtros Restritivos:</span>
          {#if filters.length === 0}
            <span class="text-muted">Nenhum filtro aplicado (Total Brasil 2022).</span>
          {:else}
            <ul class="filter-list">
              {#each filters as f}
                <li><strong>{f.dimension.toUpperCase()}</strong>: {f.operator} {JSON.stringify(f.values)}</li>
              {/each}
            </ul>
          {/if}
        </div>
      </div>
    </div>

    <!-- Card 4: Fonte de Dados e Governança -->
    <div class="def-card">
      <h4 class="card-title">Fonte & Governança</h4>
      <div class="card-content">
        <p class="field-item">
          <span class="lbl">Arquivo de Origem:</span>
          <code>bene_2022-rg8m.parquet</code>
        </p>
        <p class="field-item">
          <span class="lbl">Armazenamento:</span>
          <span>Cloudflare R2 (Edge São Paulo / GRU) via HTTPS com Range Requests</span>
        </p>
        <p class="field-item">
          <span class="lbl">Volume Auditado:</span>
          <span>81.272.978 linhas · 0 valores nulos em colunas-chave</span>
        </p>
      </div>
    </div>
  </div>

  <!-- Bloco de SQL para Transparência / Auditoria Técnica -->
  {#if sql}
    <div class="sql-transparency-section">
      <div class="sql-header">
        <div class="sql-title-box">
          <span class="sql-tag">SQL Parametrizado DuckDB</span>
          <span class="sql-desc">Instrução analítica gerada automaticamente pelo Query Planner</span>
        </div>
        <button type="button" class="btn-copy-sql" onclick={copySqlToClipboard}>
          {copiedSql ? "✓ Copiado!" : "Copiar SQL"}
        </button>
      </div>
      <pre class="sql-code-block"><code>{sql}</code></pre>
    </div>
  {/if}
</div>

<style>
  .definitions-container {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .definitions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 1rem;
  }

  .def-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .card-title {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 700;
    color: #1e293b;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 0.375rem;
  }

  .card-content {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.8125rem;
  }

  .field-item {
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    color: #334155;
  }

  .lbl {
    font-size: 0.6875rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
  }

  .badge {
    display: inline-block;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.6875rem;
    font-weight: 700;
    width: fit-content;
  }

  .badge-semi {
    background: #fef3c7;
    color: #92400e;
  }

  .badge-additive {
    background: #dcfce7;
    color: #166534;
  }

  .alert-box {
    display: flex;
    gap: 0.5rem;
    padding: 0.625rem;
    border-radius: 6px;
    font-size: 0.75rem;
    line-height: 1.35;
  }

  .alert-applied {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1e40af;
  }

  .alert-grouped {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    color: #475569;
  }

  .alert-box p {
    margin: 0.2rem 0 0 0;
  }

  .alert-icon {
    font-weight: bold;
    font-size: 0.875rem;
  }

  .filter-list {
    margin: 0.25rem 0 0 1.25rem;
    padding: 0;
    font-size: 0.75rem;
  }

  .text-muted {
    color: #94a3b8;
    font-style: italic;
  }

  .sql-transparency-section {
    background: #0f172a;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #1e293b;
  }

  .sql-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background: #1e293b;
    border-bottom: 1px solid #334155;
  }

  .sql-title-box {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .sql-tag {
    background: #3b82f6;
    color: #ffffff;
    font-size: 0.6875rem;
    font-weight: 700;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    text-transform: uppercase;
  }

  .sql-desc {
    font-size: 0.75rem;
    color: #94a3b8;
  }

  .btn-copy-sql {
    background: #334155;
    border: 1px solid #475569;
    color: #f8fafc;
    font-size: 0.75rem;
    padding: 0.25rem 0.625rem;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.15s ease;
  }

  .btn-copy-sql:hover {
    background: #475569;
  }

  .sql-code-block {
    margin: 0;
    padding: 1rem;
    color: #38bdf8;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.8125rem;
    line-height: 1.5;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
  }
</style>
