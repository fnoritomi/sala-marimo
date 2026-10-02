<script lang="ts">
  import ChartCard from "./ChartCard.svelte";
  import { formatCompact, formatNumber, formatPercent } from "../utils/formatters";

  interface OperatorItem {
    codigo_operadora: number;
    razao_social: string;
    nome_fantasia: string;
    modalidade: string;
    porte: string;
    uf_sede: string;
    vidas: number;
    sinistralidade: number;
    taxa_demandas_10k: number;
    tipo_assistencia?: string;
  }

  interface Props {
    data?: OperatorItem[];
  }

  let { data = [] }: Props = $props();

  let searchTerm = $state("");
  let sortField = $state<keyof OperatorItem>("vidas");
  let sortAsc = $state(false);

  let filteredList = $derived.by(() => {
    let list = data;
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      list = list.filter(
        (op) =>
          op.nome_fantasia.toLowerCase().includes(q) ||
          op.razao_social.toLowerCase().includes(q) ||
          op.codigo_operadora.toString().includes(q) ||
          op.modalidade.toLowerCase().includes(q)
      );
    }

    return [...list].sort((a, b) => {
      const valA = a[sortField];
      const valB = b[sortField];
      if (typeof valA === "string" && typeof valB === "string") {
        return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      return sortAsc ? Number(valA) - Number(valB) : Number(valB) - Number(valA);
    });
  });

  function handleSort(field: keyof OperatorItem) {
    if (sortField === field) {
      sortAsc = !sortAsc;
    } else {
      sortField = field;
      sortAsc = false;
    }
  }
</script>

<ChartCard
  title="Ranking das Principais Operadoras de Planos de Saúde"
  question="Quem são as operadoras líderes em vidas e qual o desempenho atuarial e de atendimento?"
  metricId="operadoras"
>
  {#snippet actions()}
    <div class="search-box">
      <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input
        type="text"
        placeholder="Buscar operadora por nome ou registro..."
        class="search-input"
        bind:value={searchTerm}
      />
    </div>
  {/snippet}

  <div class="table-container">
    <table class="operators-table">
      <thead>
        <tr>
          <th class="col-rank">#</th>
          <th class="col-op clickable" onclick={() => handleSort("nome_fantasia")}>
            Operadora {sortField === "nome_fantasia" ? (sortAsc ? "▲" : "▼") : ""}
          </th>
          <th class="col-mod clickable" onclick={() => handleSort("modalidade")}>
            Modalidade {sortField === "modalidade" ? (sortAsc ? "▲" : "▼") : ""}
          </th>
          <th class="col-porte">Porte • Sede</th>
          <th class="col-vidas clickable num-col" onclick={() => handleSort("vidas")}>
            Beneficiários {sortField === "vidas" ? (sortAsc ? "▲" : "▼") : ""}
          </th>
          <th class="col-sinistr clickable num-col" onclick={() => handleSort("sinistralidade")}>
            Sinistralidade {sortField === "sinistralidade" ? (sortAsc ? "▲" : "▼") : ""}
          </th>
          <th class="col-dem clickable num-col" onclick={() => handleSort("taxa_demandas_10k")}>
            Demandas / 10k {sortField === "taxa_demandas_10k" ? (sortAsc ? "▲" : "▼") : ""}
          </th>
        </tr>
      </thead>
      <tbody>
        {#if filteredList.length === 0}
          <tr>
            <td colspan="7" class="empty-state">Nenhuma operadora encontrada com os filtros atuais.</td>
          </tr>
        {:else}
          {#each filteredList as op, idx}
            <tr>
              <td class="col-rank">{idx + 1}</td>
              <td class="col-op">
                <div class="op-name">{op.nome_fantasia}</div>
                <div class="op-sub">Reg. ANS: {op.codigo_operadora} • {op.razao_social}</div>
              </td>
              <td class="col-mod">
                <span class="badge-modalidade">{op.modalidade}</span>
              </td>
              <td class="col-porte">
                <span class="text-porte">{op.porte}</span>
                <span class="badge-uf">{op.uf_sede}</span>
              </td>
              <td class="num-col bold-val">{formatNumber(op.vidas)}</td>
              <td class="num-col">
                <span class="badge-sinistr {op.sinistralidade > 85 ? 'sinistr-high' : 'sinistr-ok'}">
                  {op.sinistralidade.toFixed(1)}%
                </span>
              </td>
              <td class="num-col">{op.taxa_demandas_10k.toFixed(2)}</td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>
</ChartCard>

<style>
  .search-box {
    display: flex;
    align-items: center;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 0.3rem 0.6rem;
    gap: 0.4rem;
    min-width: 280px;
  }

  .search-icon {
    width: 15px;
    height: 15px;
    color: #94a3b8;
  }

  .search-input {
    border: none;
    background: transparent;
    outline: none;
    font-size: 0.8125rem;
    color: #1e293b;
    width: 100%;
  }

  .table-container {
    overflow-x: auto;
    width: 100%;
  }

  .operators-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8125rem;
    text-align: left;
  }

  .operators-table th {
    background: #f8fafc;
    padding: 0.65rem 0.85rem;
    border-bottom: 2px solid #e2e8f0;
    color: #475569;
    font-weight: 600;
    white-space: nowrap;
    user-select: none;
  }

  .operators-table th.clickable {
    cursor: pointer;
  }

  .operators-table th.clickable:hover {
    color: #2563eb;
  }

  .operators-table td {
    padding: 0.75rem 0.85rem;
    border-bottom: 1px solid #f1f5f9;
    color: #334155;
  }

  .operators-table tr:hover td {
    background: #f8fafc;
  }

  .num-col {
    text-align: right;
  }

  .bold-val {
    font-weight: 700;
    color: #0f172a;
  }

  .col-rank {
    width: 32px;
    color: #94a3b8;
    font-weight: 600;
  }

  .op-name {
    font-weight: 600;
    color: #0f172a;
  }

  .op-sub {
    font-size: 0.7rem;
    color: #94a3b8;
  }

  .badge-modalidade {
    background: #f1f5f9;
    color: #475569;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
  }

  .text-porte {
    font-size: 0.75rem;
    color: #64748b;
  }

  .badge-uf {
    background: #e2e8f0;
    color: #1e293b;
    padding: 0.15rem 0.35rem;
    border-radius: 3px;
    font-size: 0.65rem;
    font-weight: 700;
    margin-left: 0.3rem;
  }

  .badge-sinistr {
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.75rem;
  }

  .sinistr-ok {
    background: #dcfce7;
    color: #166534;
  }

  .sinistr-high {
    background: #fee2e2;
    color: #991b1b;
  }

  .empty-state {
    text-align: center;
    padding: 2rem;
    color: #94a3b8;
  }
</style>
