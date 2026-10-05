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

  interface FilterSpec {
    dimension: string;
    operator: string;
    values: any[];
  }

  interface Props {
    dimensions: Dimension[];
    filters: FilterSpec[];
    onFiltersChange: (newFilters: FilterSpec[]) => void;
  }

  let { dimensions = [], filters = [], onFiltersChange }: Props = $props();

  let isModalOpen = $state(false);
  let editingDimId = $state<string | null>(null);

  // Estado interno do editor de filtro
  let selectedDim = $derived(dimensions.find((d) => d.id === editingDimId) || null);
  let filterOperator = $state<string>("in");
  let selectedValues = $state<string[]>([]);
  let searchValueText = $state<string>("");
  let valueSearchFilter = $state<string>("");

  let filteredDimValues = $derived.by(() => {
    if (!selectedDim || !selectedDim.values) return [];
    if (!valueSearchFilter) return selectedDim.values;
    const q = valueSearchFilter.toLowerCase();
    return selectedDim.values.filter((v: any) =>
      String(v).toLowerCase().includes(q)
    );
  });

  function openFilterEditor(dimId?: string) {
    if (dimId) {
      editingDimId = dimId;
      const existing = filters.find((f) => f.dimension === dimId);
      if (existing) {
        filterOperator = existing.operator;
        selectedValues = [...existing.values];
        searchValueText = existing.operator === "like" ? String(existing.values[0] || "") : "";
      } else {
        filterOperator = "in";
        selectedValues = [];
        searchValueText = "";
      }
    } else {
      editingDimId = dimensions[0]?.id || null;
      filterOperator = "in";
      selectedValues = [];
      searchValueText = "";
    }
    isModalOpen = true;
  }

  function closeModal() {
    isModalOpen = false;
    editingDimId = null;
    selectedValues = [];
    searchValueText = "";
    valueSearchFilter = "";
  }

  function applyFilter() {
    if (!selectedDim) return;

    let newVals: any[] = [];
    let op = filterOperator;

    if (selectedDim.type === "search") {
      if (!searchValueText.trim()) {
        removeFilter(selectedDim.id);
        closeModal();
        return;
      }
      op = "like";
      newVals = [searchValueText.trim()];
    } else {
      if (selectedValues.length === 0) {
        removeFilter(selectedDim.id);
        closeModal();
        return;
      }
      newVals = [...selectedValues];
    }

    const updated = filters.filter((f) => f.dimension !== selectedDim.id);
    updated.push({
      dimension: selectedDim.id,
      operator: op,
      values: newVals,
    });
    onFiltersChange(updated);
    closeModal();
  }

  function removeFilter(dimId: string) {
    const updated = filters.filter((f) => f.dimension !== dimId);
    onFiltersChange(updated);
  }

  function toggleValue(val: string) {
    if (selectedValues.includes(val)) {
      selectedValues = selectedValues.filter((v) => v !== val);
    } else {
      selectedValues = [...selectedValues, val];
    }
  }

  function selectAllValues(vals: string[]) {
    selectedValues = Array.from(new Set([...selectedValues, ...vals]));
  }

  function clearAllValues() {
    selectedValues = [];
  }

  function getDimLabel(dimId: string): string {
    const d = dimensions.find((item) => item.id === dimId);
    return d ? d.label : dimId;
  }

  function formatFilterSummary(f: FilterSpec): string {
    if (f.operator === "like") {
      return `contém "${f.values[0]}"`;
    }
    if (f.values.length === 1) {
      return String(f.values[0]);
    }
    if (f.values.length <= 3) {
      return f.values.join(", ");
    }
    return `${f.values.slice(0, 2).join(", ")} +${f.values.length - 2} outros`;
  }
</script>

<div class="filters-container">
  <div class="filter-chips-row">
    {#each filters as f}
      <div class="filter-chip">
        <span class="chip-dim">{getDimLabel(f.dimension)}:</span>
        <span class="chip-val">{formatFilterSummary(f)}</span>
        <button
          type="button"
          class="btn-chip-action"
          onclick={() => openFilterEditor(f.dimension)}
          title="Editar filtro"
        >
          ✎
        </button>
        <button
          type="button"
          class="btn-chip-action btn-remove"
          onclick={() => removeFilter(f.dimension)}
          title="Remover filtro"
        >
          ✕
        </button>
      </div>
    {/each}

    <button
      type="button"
      class="btn-add-filter"
      onclick={() => openFilterEditor()}
    >
      <span class="icon-plus">+</span> Adicionar Filtro
    </button>
  </div>
</div>

{#if isModalOpen && selectedDim}
  <div class="modal-backdrop" onclick={closeModal} role="presentation">
    <div class="modal-dialog" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
      <div class="modal-header">
        <h4 class="modal-title">Configurar Filtro: {selectedDim.label}</h4>
        <button type="button" class="btn-close" onclick={closeModal}>✕</button>
      </div>

      <div class="modal-body">
        <!-- Seletor de Dimensão do Filtro caso queira trocar -->
        <div class="field-group">
          <label for="dim-select" class="field-label">Dimensão a Filtrar:</label>
          <select
            id="dim-select"
            class="form-select"
            value={selectedDim.id}
            onchange={(e) => {
              editingDimId = e.currentTarget.value;
              selectedValues = [];
              searchValueText = "";
            }}
          >
            {#each dimensions as d}
              <option value={d.id}>{d.label} ({d.group.toUpperCase()})</option>
            {/each}
          </select>
        </div>

        {#if selectedDim.type === "search"}
          <!-- Filtro de Busca Textual (Alta Cardinalidade: Operadora / Município) -->
          <div class="field-group">
            <label for="search-text-input" class="field-label">Pesquisar por texto / parte do nome:</label>
            <input
              id="search-text-input"
              type="text"
              class="form-input"
              placeholder="Digite o nome da operadora ou município (ex: Unimed, Bradesco, Campinas)..."
              bind:value={searchValueText}
            />
            <p class="field-hint">
              Aplica correspondência de texto sem distinção entre maiúsculas e minúsculas (`ILIKE`).
            </p>
          </div>
        {:else if selectedDim.values && selectedDim.values.length > 0}
          <!-- Filtro Categórico com Checkboxes -->
          <div class="field-group">
            <div class="values-header">
              <span class="field-label">Selecione os Valores:</span>
              <div class="actions-quick">
                <button
                  type="button"
                  class="btn-quick-link"
                  onclick={() => selectAllValues(selectedDim?.values || [])}
                >
                  Selecionar todos
                </button>
                <span>·</span>
                <button
                  type="button"
                  class="btn-quick-link"
                  onclick={clearAllValues}
                >
                  Limpar
                </button>
              </div>
            </div>

            {#if selectedDim.values.length > 8}
              <input
                type="text"
                class="form-input filter-search-input"
                placeholder="Filtrar opções abaixo..."
                bind:value={valueSearchFilter}
              />
            {/if}

            <div class="checkbox-list">
              {#each filteredDimValues as val}
                {@const checked = selectedValues.includes(String(val))}
                <label class="checkbox-item" class:checked>
                  <input
                    type="checkbox"
                    checked={checked}
                    onchange={() => toggleValue(String(val))}
                  />
                  <span class="checkbox-text">{val}</span>
                </label>
              {/each}
            </div>
            <p class="field-hint">
              {selectedValues.length} de {selectedDim.values.length} opções selecionadas.
            </p>
          </div>
        {/if}
      </div>

      <div class="modal-footer">
        <button type="button" class="btn-cancel" onclick={closeModal}>Cancelar</button>
        <button type="button" class="btn-apply" onclick={applyFilter}>Aplicar Filtro</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .filters-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .filter-chips-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
  }

  .filter-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 0.25rem 0.5rem;
    font-size: 0.8125rem;
    color: #1e293b;
  }

  .chip-dim {
    font-weight: 700;
    color: #334155;
  }

  .chip-val {
    color: #2563eb;
    max-width: 220px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .btn-chip-action {
    background: none;
    border: none;
    padding: 0 0.2rem;
    cursor: pointer;
    font-size: 0.8125rem;
    color: #64748b;
    border-radius: 3px;
  }

  .btn-chip-action:hover {
    background: #e2e8f0;
    color: #0f172a;
  }

  .btn-remove:hover {
    color: #ef4444;
  }

  .btn-add-filter {
    background: #ffffff;
    border: 1.5px dashed #cbd5e1;
    border-radius: 6px;
    padding: 0.3rem 0.625rem;
    font-size: 0.8125rem;
    font-weight: 600;
    color: #475569;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    transition: all 0.15s ease;
  }

  .btn-add-filter:hover {
    border-color: #3b82f6;
    color: #2563eb;
    background: #f8faff;
  }

  .icon-plus {
    font-size: 0.9375rem;
    font-weight: 700;
  }

  /* Modal */
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(3px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1050;
    padding: 1rem;
  }

  .modal-dialog {
    background: #ffffff;
    border-radius: 10px;
    width: 100%;
    max-width: 520px;
    max-height: 85vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
    border: 1px solid #e2e8f0;
    overflow: hidden;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
  }

  .modal-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 700;
    color: #0f172a;
  }

  .btn-close {
    background: none;
    border: none;
    font-size: 1.125rem;
    cursor: pointer;
    color: #64748b;
  }

  .modal-body {
    padding: 1.25rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    flex: 1;
  }

  .field-group {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .field-label {
    font-size: 0.8125rem;
    font-weight: 600;
    color: #334155;
  }

  .form-select, .form-input {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: 1.5px solid #cbd5e1;
    border-radius: 6px;
    font-size: 0.875rem;
    color: #1e293b;
    outline: none;
  }

  .form-select:focus, .form-input:focus {
    border-color: #2563eb;
  }

  .filter-search-input {
    margin-bottom: 0.5rem;
    padding: 0.375rem 0.5rem;
    font-size: 0.8125rem;
  }

  .values-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .actions-quick {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.75rem;
    color: #94a3b8;
  }

  .btn-quick-link {
    background: none;
    border: none;
    color: #2563eb;
    cursor: pointer;
    padding: 0;
    font-size: 0.75rem;
    text-decoration: underline;
  }

  .checkbox-list {
    max-height: 220px;
    overflow-y: auto;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    background: #fafafa;
  }

  .checkbox-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8125rem;
    color: #1e293b;
  }

  .checkbox-item:hover {
    background: #f1f5f9;
  }

  .checkbox-item.checked {
    background: #eff6ff;
    color: #1d4ed8;
    font-weight: 500;
  }

  .field-hint {
    margin: 0.25rem 0 0 0;
    font-size: 0.75rem;
    color: #64748b;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    padding: 0.875rem 1.25rem;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
  }

  .btn-cancel {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-size: 0.8125rem;
    font-weight: 500;
    color: #475569;
    cursor: pointer;
  }

  .btn-apply {
    background: #2563eb;
    border: 1px solid #1d4ed8;
    border-radius: 6px;
    padding: 0.5rem 1.25rem;
    font-size: 0.8125rem;
    font-weight: 600;
    color: #ffffff;
    cursor: pointer;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }

  .btn-apply:hover {
    background: #1d4ed8;
  }
</style>
