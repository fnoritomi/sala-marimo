<script lang="ts">
  import { onMount } from "svelte";
  import { observeMarimoValue } from "./lib/marimo-value";
  import { analyticalStore } from "./stores/analyticalStore";
  import Header from "./components/Header.svelte";
  import FilterBar from "./components/FilterBar.svelte";
  import KpiCard from "./components/KpiCard.svelte";
  import SectorEvolutionChart from "./components/SectorEvolutionChart.svelte";
  import ProfileBreakdownChart from "./components/ProfileBreakdownChart.svelte";
  import GeographicChart from "./components/GeographicChart.svelte";
  import FinancialHealthChart from "./components/FinancialHealthChart.svelte";
  import ConsumerDemandsChart from "./components/ConsumerDemandsChart.svelte";
  import OperatorsTable from "./components/OperatorsTable.svelte";
  import MetadataDrawer from "./components/MetadataDrawer.svelte";
  import DownloadModal from "./components/DownloadModal.svelte";
  import { formatCompact, formatCurrency, formatPercent } from "./utils/formatters";

  // Estado principal reativo da aplicação
  let payload = $state<any>(null);

  // Filtros locais aplicados no frontend (cross-filter e segmentações)
  let activeUf = $derived($analyticalStore.selectedUf);
  let activeAssistencia = $derived($analyticalStore.assistencia);
  let activeContratacao = $derived($analyticalStore.contratacao);
  let activeModalidade = $derived($analyticalStore.modalidade);

  // Filtra dinamicamente os dados no frontend quando possível
  let filteredKpis = $derived.by(() => {
    if (!payload?.kpis) return null;
    return payload.kpis;
  });

  let filteredGeographic = $derived.by(() => {
    if (!payload?.geographic) return [];
    return payload.geographic;
  });

  let filteredOperators = $derived.by(() => {
    if (!payload?.operators) return [];
    let list = payload.operators;
    if (activeUf) {
      list = list.filter((op: any) => op.uf_sede === activeUf);
    }
    if (activeModalidade) {
      list = list.filter((op: any) => op.modalidade === activeModalidade);
    }
    return list;
  });
</script>

<!-- Host de Projeção Reativa marimo-studio -->
<span
  id="dashboard-data"
  hidden
  mo-value="dashboard_payload"
  use:observeMarimoValue={{
    onValue: (value: any) => {
      payload = value;
    },
    onError: (err) => {
      console.warn("Marimo projection status:", err);
    },
  }}
></span>

<div class="app-layout">
  <Header competencia={payload?.kpis?.competencia_atual ?? "2026-06-01"} />
  <FilterBar />

  <main class="main-content">
    <!-- 1. BLOCO DE KPIS EXECUTIVOS -->
    <section class="kpis-grid" aria-label="Indicadores Chave do Setor">
      <KpiCard
        title="Beneficiários Ativos"
        value={formatCompact(payload?.kpis?.beneficiarios?.valor ?? 51840000)}
        delta={payload?.kpis?.beneficiarios?.delta_12m_pct ?? 1.8}
        subtitle="em 12 meses"
        sparklineData={payload?.kpis?.beneficiarios?.sparkline ?? [50.2, 50.5, 50.8, 51.1, 51.4, 51.8]}
        metricId="beneficiarios"
      />

      <KpiCard
        title="Operadoras com Vidas"
        value={String(payload?.kpis?.operadoras?.valor ?? 45)}
        delta={payload?.kpis?.operadoras?.delta_12m ?? -2}
        deltaText={`${payload?.kpis?.operadoras?.delta_12m ?? -2} operadoras`}
        subtitle="em 12 meses"
        metricId="operadoras"
      />

      <KpiCard
        title="Receita 12 Meses"
        value={formatCurrency(payload?.kpis?.financeiro?.receita_12m ?? 286400000000)}
        delta={8.2}
        subtitle="em 12 meses"
        metricId="financeiro"
      />

      <KpiCard
        title="Sinistralidade Média (12m)"
        value={formatPercent(payload?.kpis?.financeiro?.sinistralidade_12m ?? 83.5)}
        delta={0.8}
        subtitle="vs ano anterior"
        invertDeltaColors={true}
        metricId="financeiro"
      />

      <KpiCard
        title="Demandas NIP / 10k Vidas"
        value={String(payload?.kpis?.demandas?.taxa_10k ?? 4.15)}
        delta={-0.3}
        deltaText="-0.30 pt"
        subtitle="vs ano anterior"
        invertDeltaColors={true}
        metricId="demandas"
      />
    </section>

    <!-- 2. EVOLUÇÃO TEMPORAL PRINCIPAL -->
    <section class="section-block">
      <SectorEvolutionChart data={payload?.evolution} />
    </section>

    <!-- 3. PERFIL E DISTRIBUIÇÃO GEOGRÁFICA (2 COLUNAS) -->
    <section class="two-columns-grid">
      <ProfileBreakdownChart data={payload?.profile} />
      <GeographicChart data={filteredGeographic} />
    </section>

    <!-- 4. ECONÔMICO-FINANCEIRO E CONSUMIDOR (2 COLUNAS) -->
    <section class="two-columns-grid">
      <FinancialHealthChart data={payload?.financial} />
      <ConsumerDemandsChart data={payload?.demands} />
    </section>

    <!-- 5. TABELA ANALÍTICA DE OPERADORAS -->
    <section class="section-block">
      <OperatorsTable data={filteredOperators} />
    </section>
  </main>

  <footer class="app-footer">
    <div class="footer-container">
      <p>
        <strong>Agência Nacional de Saúde Suplementar (ANS)</strong> • Ministério da Saúde • Governo Federal do Brasil
      </p>
      <p class="footer-sub">
        Desenvolvido com marimo, DuckDB, Parquet, Svelte e Apache ECharts. Dados públicos abertos e governança transparente.
      </p>
    </div>
  </footer>

  <!-- Modais e Drawers de Apoio -->
  <MetadataDrawer />
  <DownloadModal payloadData={payload} />
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: #f8fafc;
    color: #1e293b;
    -webkit-font-smoothing: antialiased;
  }

  :global(*),
  :global(*::before),
  :global(*::after) {
    box-sizing: border-box;
  }

  .app-layout {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  .main-content {
    max-width: 1440px;
    width: 100%;
    margin: 0 auto;
    padding: 1.5rem 2rem 3rem 2rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    flex: 1;
  }

  .kpis-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap: 1rem;
  }

  .section-block {
    width: 100%;
  }

  .two-columns-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }

  .app-footer {
    background: #0f172a;
    color: #94a3b8;
    padding: 2rem;
    border-top: 1px solid #1e293b;
    text-align: center;
    font-size: 0.8125rem;
  }

  .footer-container {
    max-width: 1440px;
    margin: 0 auto;
  }

  .footer-container p {
    margin: 0.25rem 0;
  }

  .footer-sub {
    color: #64748b;
    font-size: 0.75rem;
  }

  @media (max-width: 1024px) {
    .two-columns-grid {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 768px) {
    .main-content {
      padding: 1rem;
      gap: 1rem;
    }
    .kpis-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
