<script lang="ts">
  import { onMount } from "svelte";

  interface Dimension {
    id: string;
    group: string;
    label: string;
    type: string;
    cardinality: number;
    values?: any[];
  }

  interface Group {
    id: string;
    label: string;
    icon?: string;
  }

  interface Props {
    title?: string;
    dimensions: Dimension[];
    groups: Group[];
    selectedIds?: string[];
    onSelect: (dimId: string) => void;
    onClose: () => void;
  }

  let {
    title = "Adicionar Dimensão",
    dimensions = [],
    groups = [],
    selectedIds = [],
    onSelect,
    onClose,
  }: Props = $props();

  let searchQuery = $state("");
  let selectedGroupFilter = $state<string>("all");
  let searchInputRef: HTMLInputElement | null = null;

  onMount(() => {
    searchInputRef?.focus();
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  });

  let filteredDimensions = $derived.by(() => {
    const q = searchQuery.toLowerCase().trim();
    return dimensions.filter((d) => {
      if (selectedGroupFilter !== "all" && d.group !== selectedGroupFilter) {
        return false;
      }
      if (!q) return true;
      return (
        d.label.toLowerCase().includes(q) ||
        d.id.toLowerCase().includes(q) ||
        d.group.toLowerCase().includes(q)
      );
    });
  });

  function getGroupLabel(groupId: string): string {
    const g = groups.find((grp) => grp.id === groupId);
    return g ? g.label : groupId.toUpperCase();
  }
</script>

<div class="modal-backdrop" onclick={onClose} role="presentation">
  <div class="modal-card" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="picker-title">
    <div class="modal-header">
      <div>
        <h3 id="picker-title" class="modal-title">{title}</h3>
        <p class="modal-sub">Selecione uma dimensão analítica do catálogo semântico da ANS</p>
      </div>
      <button type="button" class="btn-close" onclick={onClose} aria-label="Fechar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-close">
          <path d="M18 6L6 18M6 6l12 12"/>
        </svg>
      </button>
    </div>

    <!-- Barra de busca -->
    <div class="search-box">
      <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/>
        <path d="m21 21-4.3-4.3"/>
      </svg>
      <input
        bind:this={searchInputRef}
        type="text"
        placeholder="Buscar dimensão por nome ou grupo (ex: faixa, operadora, UF)..."
        bind:value={searchQuery}
        class="search-input"
      />
      {#if searchQuery}
        <button type="button" class="btn-clear-search" onclick={() => (searchQuery = "")}>✕</button>
      {/if}
    </div>

    <!-- Filtro rápido por grupos semânticos -->
    <div class="group-filters">
      <button
        type="button"
        class="group-tag"
        class:active={selectedGroupFilter === "all"}
        onclick={() => (selectedGroupFilter = "all")}
      >
        Todas ({dimensions.length})
      </button>
      {#each groups as g}
        {@const count = dimensions.filter((d) => d.group === g.id).length}
        <button
          type="button"
          class="group-tag"
          class:active={selectedGroupFilter === g.id}
          onclick={() => (selectedGroupFilter = g.id)}
        >
          {g.label} ({count})
        </button>
      {/each}
    </div>

    <!-- Lista de dimensões -->
    <div class="dimensions-list">
      {#if filteredDimensions.length === 0}
        <div class="empty-state">
          <p>Nenhuma dimensão encontrada para "<strong>{searchQuery}</strong>".</p>
        </div>
      {:else}
        {#each filteredDimensions as dim}
          {@const isAlreadySelected = selectedIds.includes(dim.id)}
          <button
            type="button"
            class="dim-item-card"
            class:is-selected={isAlreadySelected}
            onclick={() => {
              if (!isAlreadySelected) {
                onSelect(dim.id);
                onClose();
              }
            }}
            disabled={isAlreadySelected}
          >
            <div class="dim-item-left">
              <span class="group-badge group-{dim.group}">{getGroupLabel(dim.group)}</span>
              <span class="dim-name">{dim.label}</span>
            </div>
            <div class="dim-item-right">
              {#if dim.cardinality > 0}
                <span class="cardinality-badge" title="Número estimado de categorias distintas">
                  ~{dim.cardinality.toLocaleString("pt-BR")} valores
                </span>
              {/if}
              {#if isAlreadySelected}
                <span class="status-added">Já adicionada</span>
              {:else}
                <span class="btn-select-action">+ Adicionar</span>
              {/if}
            </div>
          </button>
        {/each}
      {/if}
    </div>
  </div>
</div>

<style>
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.65);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 1rem;
  }

  .modal-card {
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 680px;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    border: 1px solid #e2e8f0;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid #f1f5f9;
    background: #f8fafc;
  }

  .modal-title {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
  }

  .modal-sub {
    margin: 0.25rem 0 0 0;
    font-size: 0.8125rem;
    color: #64748b;
  }

  .btn-close {
    background: none;
    border: none;
    padding: 0.375rem;
    border-radius: 6px;
    cursor: pointer;
    color: #64748b;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
  }

  .btn-close:hover {
    background: #e2e8f0;
    color: #0f172a;
  }

  .icon-close {
    width: 1.25rem;
    height: 1.25rem;
  }

  .search-box {
    position: relative;
    padding: 1rem 1.5rem 0.5rem 1.5rem;
    display: flex;
    align-items: center;
  }

  .search-icon {
    position: absolute;
    left: 2.25rem;
    width: 1.125rem;
    height: 1.125rem;
    color: #94a3b8;
  }

  .search-input {
    width: 100%;
    padding: 0.625rem 2.25rem 0.625rem 2.5rem;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    font-size: 0.875rem;
    color: #1e293b;
    outline: none;
    transition: border-color 0.15s ease;
  }

  .search-input:focus {
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
  }

  .btn-clear-search {
    position: absolute;
    right: 2.25rem;
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 1rem;
  }

  .group-filters {
    display: flex;
    flex-wrap: wrap;
    gap: 0.375rem;
    padding: 0.5rem 1.5rem 0.75rem 1.5rem;
    border-bottom: 1px solid #f1f5f9;
  }

  .group-tag {
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 0.25rem 0.625rem;
    font-size: 0.75rem;
    font-weight: 500;
    color: #475569;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .group-tag:hover {
    background: #e2e8f0;
    color: #0f172a;
  }

  .group-tag.active {
    background: #1e3a8a;
    border-color: #1e3a8a;
    color: #ffffff;
  }

  .dimensions-list {
    padding: 0.75rem 1.5rem 1.5rem 1.5rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    flex: 1;
  }

  .dim-item-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    background: #ffffff;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s ease;
  }

  .dim-item-card:hover:not(:disabled) {
    border-color: #3b82f6;
    background: #f8faff;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
  }

  .dim-item-card.is-selected {
    opacity: 0.6;
    background: #f8fafc;
    cursor: not-allowed;
  }

  .dim-item-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .group-badge {
    font-size: 0.6875rem;
    font-weight: 700;
    text-transform: uppercase;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    letter-spacing: 0.025em;
  }

  .group-tempo { background: #e0f2fe; color: #0369a1; }
  .group-beneficiario { background: #fce7f3; color: #be185d; }
  .group-localizacao { background: #dcfce7; color: #15803d; }
  .group-plano { background: #ede9fe; color: #6d28d9; }
  .group-operadora { background: #ffedd5; color: #c2410c; }

  .dim-name {
    font-size: 0.875rem;
    font-weight: 600;
    color: #1e293b;
  }

  .dim-item-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .cardinality-badge {
    font-size: 0.75rem;
    color: #64748b;
    background: #f1f5f9;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
  }

  .status-added {
    font-size: 0.75rem;
    color: #94a3b8;
    font-weight: 500;
  }

  .btn-select-action {
    font-size: 0.75rem;
    font-weight: 600;
    color: #2563eb;
    background: #eff6ff;
    padding: 0.25rem 0.625rem;
    border-radius: 6px;
    border: 1px solid #bfdbfe;
  }

  .empty-state {
    text-align: center;
    padding: 2.5rem 1rem;
    color: #64748b;
    font-size: 0.875rem;
  }
</style>
