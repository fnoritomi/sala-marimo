<script lang="ts">
  import { analyticalStore } from "../stores/analyticalStore";

  interface Props {
    competencia?: string;
    activeTab?: "overview" | "explorer";
    onTabChange?: (tab: "overview" | "explorer") => void;
  }

  let {
    competencia = "2026-06-01",
    activeTab = "overview",
    onTabChange,
  }: Props = $props();
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
        <h1 class="main-title">Sala de Situação da Saúde Suplementar</h1>
        <p class="subtitle">Visão Panorâmica, Monitoramento e Inteligência Regulatória</p>
      </div>
    </div>

    <!-- Navegação Principal por Abas -->
    <nav class="nav-tabs-center" aria-label="Seções da Aplicação">
      <button
        type="button"
        class="nav-tab-btn"
        class:active={activeTab === "overview"}
        onclick={() => onTabChange?.("overview")}
      >
        <span class="tab-icon">📊</span> Visão do Setor
      </button>
      <button
        type="button"
        class="nav-tab-btn"
        class:active={activeTab === "explorer"}
        onclick={() => onTabChange?.("explorer")}
      >
        <span class="tab-icon">🔍</span> Explorar Beneficiários
      </button>
    </nav>

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

  .btn-header-secondary {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
    background: #1e293b;
    color: #e2e8f0;
    border: 1px solid #475569;
  }

  .btn-header-secondary:hover {
    background: #334155;
    color: #ffffff;
  }

  .btn-icon {
    width: 16px;
    height: 16px;
  }

  .nav-tabs-center {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: #0b1120;
    padding: 0.25rem;
    border-radius: 8px;
    border: 1px solid #1e293b;
  }

  .nav-tab-btn {
    background: none;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.8125rem;
    font-weight: 600;
    color: #94a3b8;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    transition: all 0.15s ease;
  }

  .nav-tab-btn:hover {
    color: #f8fafc;
    background: #1e293b;
  }

  .nav-tab-btn.active {
    background: #1e3a8a;
    color: #ffffff;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  }

  .tab-icon {
    font-size: 0.9375rem;
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
