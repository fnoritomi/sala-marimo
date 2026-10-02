<script lang="ts">
  import { analyticalStore } from "../stores/analyticalStore";

  interface Props {
    competencia?: string;
  }

  let { competencia = "2026-06-01" }: Props = $props();
</script>

<header class="app-header">
  <div class="header-container">
    <div class="brand-section">
      <div class="logo-box">
        <svg class="ans-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="m9 12 2 2 4-4"/>
        </svg>
      </div>
      <div>
        <div class="gov-label">Governo Federal • Agência Nacional de Saúde Suplementar</div>
        <h1 class="main-title">Sala de Situação da Saúde Suplementar</h1>
        <p class="subtitle">Visão Panorâmica, Monitoramento e Inteligência Regulatória</p>
      </div>
    </div>

    <div class="actions-section">
      <div class="badge-competence">
        <span class="pulse-dot"></span>
        <span>Competência: <strong>{competencia}</strong></span>
      </div>

      <button
        type="button"
        class="btn-header-secondary"
        onclick={() => analyticalStore.openMetadata("geral")}
        title="Ver informações metodológicas e fontes"
      >
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 16v-4"/>
          <path d="M12 8h.01"/>
        </svg>
        Metodologia
      </button>

      <button
        type="button"
        class="btn-header-primary"
        onclick={() => analyticalStore.setDownloadOpen(true)}
        title="Exportar dados analíticos"
      >
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        Download Dados
      </button>
    </div>
  </div>
</header>

<style>
  .app-header {
    background: #0f172a;
    color: #ffffff;
    border-bottom: 3px solid #1e3a8a;
    padding: 1.25rem 2rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .header-container {
    max-width: 1440px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1.5rem;
  }

  .brand-section {
    display: flex;
    align-items: center;
    gap: 1.25rem;
  }

  .logo-box {
    background: #1e3a8a;
    color: #38bdf8;
    width: 48px;
    height: 48px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .ans-icon {
    width: 28px;
    height: 28px;
  }

  .gov-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94a3b8;
    margin-bottom: 0.25rem;
  }

  .main-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
    color: #f8fafc;
    letter-spacing: -0.02em;
  }

  .subtitle {
    font-size: 0.875rem;
    color: #cbd5e1;
    margin: 0.2rem 0 0 0;
  }

  .actions-section {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .badge-competence {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: #1e293b;
    border: 1px solid #334155;
    padding: 0.4rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.8125rem;
    color: #e2e8f0;
  }

  .pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 8px #10b981;
  }

  .btn-header-secondary,
  .btn-header-primary {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
  }

  .btn-header-secondary {
    background: #1e293b;
    color: #e2e8f0;
    border: 1px solid #475569;
  }

  .btn-header-secondary:hover {
    background: #334155;
    color: #ffffff;
  }

  .btn-header-primary {
    background: #2563eb;
    color: #ffffff;
    border: 1px solid #3b82f6;
  }

  .btn-header-primary:hover {
    background: #1d4ed8;
  }

  .btn-icon {
    width: 16px;
    height: 16px;
  }

  @media (max-width: 768px) {
    .app-header {
      padding: 1rem;
    }
    .header-container {
      flex-direction: column;
      align-items: flex-start;
    }
  }
</style>
