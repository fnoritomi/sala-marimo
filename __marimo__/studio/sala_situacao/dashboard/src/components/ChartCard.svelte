<script lang="ts">
  import type { Snippet } from "svelte";
  import { analyticalStore } from "../stores/analyticalStore";

  interface Props {
    title: string;
    question?: string;
    metricId?: string;
    onDownload?: () => void;
    actions?: Snippet;
    children?: Snippet;
  }

  let { title, question, metricId, onDownload, actions, children }: Props = $props();
</script>

<div class="chart-card">
  <div class="chart-header">
    <div class="title-group">
      <div class="title-row">
        <h3 class="chart-title">{title}</h3>
        {#if metricId}
          <button
            type="button"
            class="btn-info"
            onclick={() => analyticalStore.openMetadata(metricId)}
            title="Ver definição e metodologia"
          >
            ⓘ
          </button>
        {/if}
      </div>
      {#if question}
        <p class="chart-question">{question}</p>
      {/if}
    </div>

    {#if actions || onDownload}
      <div class="chart-actions">
        {#if actions}
          {@render actions()}
        {/if}
        {#if onDownload}
          <button
            type="button"
            class="btn-card-download"
            onclick={onDownload}
            title="Baixar dados visualizados em CSV"
            aria-label="Baixar dados visualizados em CSV"
          >
            <svg class="icon-download" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            <span>CSV</span>
          </button>
        {/if}
      </div>
    {/if}
  </div>

  <div class="chart-content">
    {#if children}
      {@render children()}
    {/if}
  </div>
</div>

<style>
  .chart-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    display: flex;
    flex-direction: column;
    min-height: 380px;
    transition: box-shadow 0.15s ease;
  }

  .chart-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  }

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
  }

  .title-group {
    display: flex;
    flex-direction: column;
  }

  .title-row {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .chart-title {
    font-size: 1.0625rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
    letter-spacing: -0.01em;
  }

  .chart-question {
    font-size: 0.8125rem;
    color: #64748b;
    margin: 0.2rem 0 0 0;
  }

  .btn-info {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 0.875rem;
    padding: 0.1rem 0.3rem;
    border-radius: 4px;
    line-height: 1;
    transition: color 0.15s;
  }

  .btn-info:hover {
    color: #2563eb;
    background: #eff6ff;
  }

  .chart-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .btn-card-download {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.25rem 0.6rem;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #475569;
    cursor: pointer;
    transition: all 0.15s ease;
    height: 28px;
  }

  .btn-card-download:hover {
    background: #eff6ff;
    color: #1e40af;
    border-color: #93c5fd;
  }

  .btn-card-download:active {
    transform: scale(0.97);
  }

  .icon-download {
    width: 13px;
    height: 13px;
    color: currentColor;
  }

  .chart-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    position: relative;
    width: 100%;
    min-height: 300px;
  }
</style>
