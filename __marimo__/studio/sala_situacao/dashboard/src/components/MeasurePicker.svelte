<script lang="ts">
  interface Measure {
    id: string;
    label: string;
    type: string;
    aggregation: string;
    is_semi_additive: boolean;
    description: string;
    format: string;
  }

  interface Props {
    measures: Measure[];
    selectedMeasure: string;
    onChange: (measureId: string) => void;
  }

  let { measures = [], selectedMeasure, onChange }: Props = $props();
</script>

<div class="measure-picker-container">
  <span class="picker-label">MÉTRICA / MEDIDA:</span>
  <div class="measures-grid">
    {#each measures as m}
      {@const isSelected = m.id === selectedMeasure}
      <button
        type="button"
        class="measure-card"
        class:active={isSelected}
        onclick={() => onChange(m.id)}
        title={m.description}
      >
        <div class="measure-header">
          <span class="measure-name">{m.label}</span>
          {#if m.is_semi_additive}
            <span class="type-tag semi-tag" title="Medida semi-aditiva (snapshot). Não acumula no tempo.">Estoque (Snapshot)</span>
          {:else}
            <span class="type-tag additive-tag" title="Medida aditiva no tempo. Permite somar períodos acumulados.">Fluxo Mensal</span>
          {/if}
        </div>
        <p class="measure-desc">{m.description}</p>
      </button>
    {/each}
  </div>
</div>

<style>
  .measure-picker-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .picker-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: #475569;
    letter-spacing: 0.05em;
  }

  .measures-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 0.75rem;
  }

  .measure-card {
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    text-align: left;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .measure-card:hover {
    border-color: #94a3b8;
    background: #f8fafc;
  }

  .measure-card.active {
    border-color: #2563eb;
    background: #eff6ff;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
  }

  .measure-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
  }

  .measure-name {
    font-size: 0.875rem;
    font-weight: 700;
    color: #0f172a;
  }

  .type-tag {
    font-size: 0.6875rem;
    font-weight: 600;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    white-space: nowrap;
  }

  .semi-tag {
    background: #fef3c7;
    color: #b45309;
  }

  .additive-tag {
    background: #dcfce7;
    color: #15803d;
  }

  .measure-desc {
    margin: 0;
    font-size: 0.75rem;
    color: #64748b;
    line-height: 1.25;
  }
</style>
