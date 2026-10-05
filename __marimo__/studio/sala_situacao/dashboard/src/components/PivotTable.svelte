<script lang="ts">
  import { formatNumber, downloadCsv } from "../utils/formatters";

  interface Props {
    columns: string[];
    rows: any[][];
    measureName?: string;
    isPivoted?: boolean;
    semiAdditiveApplied?: boolean;
  }

  let {
    columns = [],
    rows = [],
    measureName = "beneficiarios",
    isPivoted = false,
    semiAdditiveApplied = false,
  }: Props = $props();

  let sortColumnIndex = $state<number | null>(null);
  let sortDirection = $state<"asc" | "desc">("asc");
  let filterText = $state<string>("");
  let pageSize = $state<number>(25);
  let currentPage = $state<number>(1);
  let copiedCellKey = $state<string | null>(null);

  // Ordenação
  function handleSort(colIdx: number) {
    if (sortColumnIndex === colIdx) {
      sortDirection = sortDirection === "asc" ? "desc" : "asc";
    } else {
      sortColumnIndex = colIdx;
      sortDirection = "desc";
    }
  }

  // Linhas filtradas pela busca rápida local
  let filteredRows = $derived.by(() => {
    if (!filterText.trim()) return rows;
    const q = filterText.toLowerCase().trim();
    return rows.filter((r) =>
      r.some((cell) => String(cell).toLowerCase().includes(q))
    );
  });

  // Linhas ordenadas
  let sortedRows = $derived.by(() => {
    if (sortColumnIndex === null) return filteredRows;
    const idx = sortColumnIndex;
    const dir = sortDirection === "asc" ? 1 : -1;

    return [...filteredRows].sort((a, b) => {
      const valA = a[idx];
      const valB = b[idx];
      if (valA === valB) return 0;
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      if (typeof valA === "number" && typeof valB === "number") {
        return (valA - valB) * dir;
      }
      return String(valA).localeCompare(String(valB)) * dir;
    });
  });

  // Paginação
  let totalPages = $derived(Math.max(1, Math.ceil(sortedRows.length / pageSize)));
  let paginatedRows = $derived(
    sortedRows.slice((currentPage - 1) * pageSize, currentPage * pageSize)
  );

  // Cálculo da Linha de Totais (quando semanticamente aplicável)
  let columnTotals = $derived.by(() => {
    if (rows.length === 0 || columns.length === 0) return null;

    // Se for semi-aditiva e não tiver filtro temporal único, alertar ou omitir
    const totals: (number | null)[] = new Array(columns.length).fill(null);

    for (let c = 0; c < columns.length; c++) {
      let isNumericCol = true;
      let sum = 0;
      for (const r of rows) {
        const val = r[c];
        if (typeof val === "number") {
          sum += val;
        } else if (val !== null && val !== undefined && val !== "") {
          isNumericCol = false;
          break;
        }
      }
      if (isNumericCol) {
        totals[c] = sum;
      }
    }
    return totals;
  });

  function isNumericColumn(colIdx: number): boolean {
    if (rows.length === 0) return false;
    const sample = rows[0][colIdx];
    return typeof sample === "number";
  }

  function formatCellValue(val: any, colIdx: number): string {
    if (val === null || val === undefined) return "-";
    if (typeof val === "number") {
      return formatNumber(val);
    }
    return String(val);
  }

  function copyToClipboard(val: any, key: string) {
    navigator.clipboard?.writeText(String(val));
    copiedCellKey = key;
    setTimeout(() => {
      if (copiedCellKey === key) copiedCellKey = null;
    }, 1500);
  }

  function handleExportCsv() {
    downloadCsv(`consulta_beneficiarios_${new Date().toISOString().slice(0, 10)}.csv`, columns, rows);
  }
</script>

<div class="pivot-table-container">
  <!-- Barra de Ferramentas Superior da Tabela -->
  <div class="table-toolbar">
    <div class="toolbar-left">
      <input
        type="text"
        placeholder="Filtrar dados na tabela..."
        bind:value={filterText}
        class="input-filter-table"
      />
      <span class="rows-count">
        Mostrando <strong>{sortedRows.length.toLocaleString("pt-BR")}</strong> de {rows.length.toLocaleString("pt-BR")} linhas
      </span>
    </div>

    <div class="toolbar-right">
      <div class="page-size-selector">
        <label for="page-size-select">Linhas por pág:</label>
        <select id="page-size-select" bind:value={pageSize} onchange={() => (currentPage = 1)}>
          <option value={15}>15</option>
          <option value={25}>25</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </div>

      <button type="button" class="btn-export" onclick={handleExportCsv} title="Baixar CSV com todos os dados da consulta">
        <svg class="icon-download" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        Exportar CSV
      </button>
    </div>
  </div>

  <!-- Tabela com Cabeçalho Fixo -->
  <div class="table-wrapper">
    <table class="ans-tabular-grid">
      <thead>
        <tr>
          {#each columns as col, cIdx}
            {@const isNumeric = isNumericColumn(cIdx)}
            {@const isSorted = sortColumnIndex === cIdx}
            {@const isTotalCol = col === "Total"}
            <th
              class="grid-th"
              class:align-right={isNumeric}
              class:is-total={isTotalCol}
              onclick={() => handleSort(cIdx)}
            >
              <div class="th-content" class:justify-right={isNumeric}>
                <span>{col}</span>
                <span class="sort-indicator">
                  {#if isSorted}
                    {sortDirection === "asc" ? "▲" : "▼"}
                  {:else}
                    <span class="sort-ghost">↕</span>
                  {/if}
                </span>
              </div>
            </th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#if paginatedRows.length === 0}
          <tr>
            <td colspan={columns.length} class="empty-cell">
              Nenhum registro encontrado.
            </td>
          </tr>
        {:else}
          {#each paginatedRows as row, rIdx}
            <tr class="grid-tr">
              {#each row as cell, cIdx}
                {@const isNumeric = typeof cell === "number"}
                {@const isTotalCol = columns[cIdx] === "Total"}
                {@const cellKey = `${rIdx}-${cIdx}`}
                <td
                  class="grid-td"
                  class:align-right={isNumeric}
                  class:is-total={isTotalCol}
                  onclick={() => copyToClipboard(cell, cellKey)}
                  title="Clique para copiar valor"
                >
                  <span class="cell-text">{formatCellValue(cell, cIdx)}</span>
                  {#if copiedCellKey === cellKey}
                    <span class="copied-badge">Copiado!</span>
                  {/if}
                </td>
              {/each}
            </tr>
          {/each}
        {/if}
      </tbody>
      {#if columnTotals && columnTotals.some((t) => t !== null)}
        <tfoot>
          <tr class="grid-tfoot-row">
            {#each columnTotals as tot, cIdx}
              <td class="grid-tf" class:align-right={tot !== null}>
                {#if cIdx === 0 && tot === null}
                  <strong>Total Geral</strong>
                {:else if tot !== null}
                  <strong>{formatNumber(tot)}</strong>
                {:else}
                  -
                {/if}
              </td>
            {/each}
          </tr>
        </tfoot>
      {/if}
    </table>
  </div>

  <!-- Paginação Inferior -->
  {#if totalPages > 1}
    <div class="pagination-footer">
      <div class="page-info">
        Página <strong>{currentPage}</strong> de <strong>{totalPages}</strong>
      </div>
      <div class="pagination-buttons">
        <button
          type="button"
          class="btn-page"
          disabled={currentPage === 1}
          onclick={() => (currentPage = 1)}
        >
          ⇤
        </button>
        <button
          type="button"
          class="btn-page"
          disabled={currentPage === 1}
          onclick={() => (currentPage -= 1)}
        >
          ← Anterior
        </button>
        <button
          type="button"
          class="btn-page"
          disabled={currentPage === totalPages}
          onclick={() => (currentPage += 1)}
        >
          Próxima →
        </button>
        <button
          type="button"
          class="btn-page"
          disabled={currentPage === totalPages}
          onclick={() => (currentPage = totalPages)}
        >
          ⇥
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  .pivot-table-container {
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
  }

  .table-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .toolbar-left, .toolbar-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .input-filter-table {
    padding: 0.375rem 0.625rem;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-size: 0.8125rem;
    width: 220px;
    outline: none;
  }

  .input-filter-table:focus {
    border-color: #2563eb;
  }

  .rows-count {
    font-size: 0.75rem;
    color: #64748b;
  }

  .page-size-selector {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.75rem;
    color: #475569;
  }

  .page-size-selector select {
    padding: 0.25rem 0.5rem;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    font-size: 0.75rem;
    background: #ffffff;
  }

  .btn-export {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 0.375rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: #1e293b;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-export:hover {
    background: #f1f5f9;
    border-color: #94a3b8;
  }

  .icon-download {
    width: 0.875rem;
    height: 0.875rem;
    color: #2563eb;
  }

  .table-wrapper {
    max-height: 520px;
    overflow: auto;
  }

  .ans-tabular-grid {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.8125rem;
    text-align: left;
  }

  .grid-th {
    position: sticky;
    top: 0;
    background: #f1f5f9;
    color: #1e293b;
    font-weight: 700;
    padding: 0.625rem 0.875rem;
    border-bottom: 2px solid #cbd5e1;
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
    z-index: 10;
  }

  .grid-th:hover {
    background: #e2e8f0;
  }

  .grid-th.is-total {
    background: #e0f2fe;
    color: #0369a1;
  }

  .th-content {
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }

  .justify-right {
    justify-content: flex-end;
  }

  .sort-indicator {
    font-size: 0.6875rem;
    color: #2563eb;
  }

  .sort-ghost {
    color: #94a3b8;
    opacity: 0.4;
  }

  .grid-tr {
    transition: background-color 0.1s ease;
  }

  .grid-tr:hover {
    background-color: #f8faff;
  }

  .grid-tr:nth-child(even) {
    background-color: #fafafa;
  }

  .grid-tr:nth-child(even):hover {
    background-color: #f8faff;
  }

  .grid-td {
    position: relative;
    padding: 0.5rem 0.875rem;
    border-bottom: 1px solid #f1f5f9;
    color: #334155;
    white-space: nowrap;
    cursor: cell;
  }

  .grid-td.is-total {
    font-weight: 700;
    background-color: rgba(224, 242, 254, 0.25);
    color: #0369a1;
  }

  .align-right {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  .cell-text {
    display: inline-block;
  }

  .copied-badge {
    position: absolute;
    right: 0.5rem;
    top: 50%;
    transform: translateY(-50%);
    background: #10b981;
    color: #ffffff;
    font-size: 0.625rem;
    font-weight: 700;
    padding: 0.15rem 0.35rem;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
  }

  .grid-tfoot-row {
    position: sticky;
    bottom: 0;
    background: #f8fafc;
    border-top: 2px solid #cbd5e1;
    font-weight: 700;
    z-index: 10;
  }

  .grid-tf {
    padding: 0.625rem 0.875rem;
    border-top: 2px solid #cbd5e1;
    color: #0f172a;
    white-space: nowrap;
  }

  .empty-cell {
    text-align: center;
    padding: 3rem 1rem;
    color: #64748b;
  }

  .pagination-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    font-size: 0.8125rem;
  }

  .page-info {
    color: #64748b;
  }

  .pagination-buttons {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .btn-page {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 0.25rem 0.625rem;
    font-size: 0.75rem;
    color: #334155;
    cursor: pointer;
  }

  .btn-page:hover:not(:disabled) {
    background: #f1f5f9;
    border-color: #94a3b8;
  }

  .btn-page:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
</style>
