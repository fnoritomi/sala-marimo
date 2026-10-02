<script lang="ts">
  import { analyticalStore, hasActiveFilters } from "../stores/analyticalStore";

  const modalidadesList = [
    "Todas",
    "Cooperativa médica",
    "Medicina de grupo",
    "Seguradora especializada em saúde",
    "Autogestão",
    "Filantropia",
    "Cooperativa odontológica",
    "Odontologia de grupo",
  ];

  const ufList = [
    "Todas", "SP", "RJ", "MG", "RS", "PR", "BA", "SC", "PE", "CE",
    "GO", "ES", "DF", "PA", "MT", "MA", "MS", "AM", "RN", "PB",
    "AL", "PI", "SE", "RO", "TO", "AC", "AP", "RR"
  ];
</script>

<div class="filter-bar-wrapper">
  <div class="filter-bar-container">
    <div class="filter-group">
      <label for="filter-assistencia" class="filter-label">Segmentação Assistencial</label>
      <select
        id="filter-assistencia"
        class="filter-select"
        value={$analyticalStore.assistencia ?? "Todas"}
        onchange={(e) => analyticalStore.setAssistencia(e.currentTarget.value)}
      >
        <option value="Todas">Todas as Coberturas</option>
        <option value="Médica">Médico-Hospitalar</option>
        <option value="Odontológica">Exclusivamente Odontológica</option>
      </select>
    </div>

    <div class="filter-group">
      <label for="filter-contratacao" class="filter-label">Tipo de Contratação</label>
      <select
        id="filter-contratacao"
        class="filter-select"
        value={$analyticalStore.contratacao ?? "Todas"}
        onchange={(e) => analyticalStore.setContratacao(e.currentTarget.value)}
      >
        <option value="Todas">Todas as Contratações</option>
        <option value="Coletivo Empresarial">Coletivo Empresarial</option>
        <option value="Individual ou Familiar">Individual ou Familiar</option>
        <option value="Coletivo por Adesão">Coletivo por Adesão</option>
      </select>
    </div>

    <div class="filter-group">
      <label for="filter-modalidade" class="filter-label">Modalidade da Operadora</label>
      <select
        id="filter-modalidade"
        class="filter-select"
        value={$analyticalStore.modalidade ?? "Todas"}
        onchange={(e) => analyticalStore.setModalidade(e.currentTarget.value)}
      >
        {#each modalidadesList as mod}
          <option value={mod}>{mod === "Todas" ? "Todas as Modalidades" : mod}</option>
        {/each}
      </select>
    </div>

    <div class="filter-group">
      <label for="filter-uf" class="filter-label">Estado (UF)</label>
      <select
        id="filter-uf"
        class="filter-select"
        value={$analyticalStore.selectedUf ?? "Todas"}
        onchange={(e) => analyticalStore.setUf(e.currentTarget.value)}
      >
        {#each ufList as uf}
          <option value={uf}>{uf === "Todas" ? "Brasil (Todas as UFs)" : uf}</option>
        {/each}
      </select>
    </div>

    {#if $hasActiveFilters}
      <button
        type="button"
        class="btn-clear-all"
        onclick={() => analyticalStore.clearAll()}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-clear">
          <path d="M3 6h18"/>
          <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
          <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
        </svg>
        Limpar Filtros
      </button>
    {/if}
  </div>

  <!-- Active Filter Chips Area -->
  {#if $hasActiveFilters}
    <div class="active-chips-area">
      <span class="chips-label">Filtros ativos:</span>
      
      {#if $analyticalStore.selectedUf}
        <span class="filter-chip highlight-chip">
          <strong>UF:</strong> {$analyticalStore.selectedUf}
          <button
            type="button"
            class="chip-close"
            onclick={() => analyticalStore.clearUf()}
            title="Remover filtro de UF"
          >✕</button>
        </span>
      {/if}

      {#if $analyticalStore.assistencia}
        <span class="filter-chip">
          <strong>Assistência:</strong> {$analyticalStore.assistencia}
          <button
            type="button"
            class="chip-close"
            onclick={() => analyticalStore.setAssistencia(null)}
          >✕</button>
        </span>
      {/if}

      {#if $analyticalStore.contratacao}
        <span class="filter-chip">
          <strong>Contratação:</strong> {$analyticalStore.contratacao}
          <button
            type="button"
            class="chip-close"
            onclick={() => analyticalStore.setContratacao(null)}
          >✕</button>
        </span>
      {/if}

      {#if $analyticalStore.modalidade}
        <span class="filter-chip">
          <strong>Modalidade:</strong> {$analyticalStore.modalidade}
          <button
            type="button"
            class="chip-close"
            onclick={() => analyticalStore.setModalidade(null)}
          >✕</button>
        </span>
      {/if}
    </div>
  {/if}
</div>

<style>
  .filter-bar-wrapper {
    background: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 1rem 2rem;
    position: sticky;
    top: 0;
    z-index: 40;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .filter-bar-container {
    max-width: 1440px;
    margin: 0 auto;
    display: flex;
    align-items: flex-end;
    gap: 1.25rem;
    flex-wrap: wrap;
  }

  .filter-group {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    min-width: 200px;
    flex: 1;
  }

  .filter-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #475569;
  }

  .filter-select {
    padding: 0.5rem 0.75rem;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-size: 0.875rem;
    color: #1e293b;
    outline: none;
    transition: all 0.15s ease;
  }

  .filter-select:focus {
    border-color: #2563eb;
    background: #ffffff;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
  }

  .btn-clear-all {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.525rem 0.875rem;
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #fecaca;
    border-radius: 6px;
    font-size: 0.8125rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
    height: 38px;
  }

  .btn-clear-all:hover {
    background: #fca5a5;
  }

  .icon-clear {
    width: 15px;
    height: 15px;
  }

  .active-chips-area {
    max-width: 1440px;
    margin: 0.75rem auto 0 auto;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .chips-label {
    font-size: 0.8125rem;
    font-weight: 500;
    color: #64748b;
  }

  .filter-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    color: #334155;
  }

  .highlight-chip {
    background: #eff6ff;
    border-color: #bfdbfe;
    color: #1e40af;
    font-weight: 600;
  }

  .chip-close {
    background: none;
    border: none;
    cursor: pointer;
    color: inherit;
    font-size: 0.75rem;
    padding: 0;
    margin-left: 0.2rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .chip-close:hover {
    opacity: 0.7;
  }

  @media (max-width: 768px) {
    .filter-bar-wrapper {
      padding: 0.75rem 1rem;
    }
  }
</style>
