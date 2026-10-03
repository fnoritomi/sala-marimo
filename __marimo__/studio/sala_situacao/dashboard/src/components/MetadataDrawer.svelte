<script lang="ts">
  import { analyticalStore } from "../stores/analyticalStore";

  const METADATA_DICTIONARY: Record<
    string,
    {
      titulo: string;
      definicao: string;
      fonte: string;
      periodicidade: string;
      unidade: string;
      metodologia: string;
      observacoes: string;
    }
  > = {
    geral: {
      titulo: "Sala de Situação da Saúde Suplementar - Metodologia Geral",
      definicao: "Painel executivo de monitoramento analítico do mercado de planos privados de assistência à saúde no Brasil.",
      fonte: "Sistemas Setoriais Regulatórios (SIB, DIOPS, NIP, CADOP) e IBGE",
      periodicidade: "Mensal (SIB/NIP) e Trimestral (DIOPS)",
      unidade: "Múltiplas (Vidas, R$, %, Taxas)",
      metodologia: "Consolidação e tabulação de dados regulatórios com respeito estrito a medidas de estoque (snapshot na última competência) e medidas aditivas de fluxo.",
      observacoes: "Os dados de beneficiários refletem os vínculos ativos declarados pelas operadoras no Sistema de Informações de Beneficiários (SIB).",
    },
    beneficiarios: {
      titulo: "Beneficiários Ativos (Estoque Mensal)",
      definicao: "Número total de pessoas vinculadas a contratos de planos de saúde ativos na competência.",
      fonte: "SIB/ANS (Sistema de Informações de Beneficiários)",
      periodicidade: "Mensal",
      unidade: "Vidas / Pessoas",
      metodologia: "Medida semi-aditiva (snapshot). Ao avaliar períodos acumulados (trimestre, ano), considera-se a posição da última competência válida do intervalo, nunca a soma temporal dos meses.",
      observacoes: "Vidas em planos exclusivamente odontológicos e médico-hospitalares são segregadas para evitar dupla contagem de um mesmo cidadão.",
    },
    operadoras: {
      titulo: "Operadoras Ativas com Beneficiários",
      definicao: "Total de pessoas jurídicas registradas na ANS com autorização de funcionamento e que possuem carteira de clientes ativos.",
      fonte: "CADOP/ANS (Cadastro de Operadoras)",
      periodicidade: "Mensal",
      unidade: "Operadoras",
      metodologia: "Contagem distinta (COUNT DISTINCT) de registros ANS que reportaram movimentação de vínculos na competência.",
      observacoes: "Exclui operadoras sob liquidação extrajudicial ou com comercialização cancelada sem vidas.",
    },
    financeiro: {
      titulo: "Receitas, Despesas e Sinistralidade",
      definicao: "Indicadores econômico-financeiros da operação de saúde suplementar.",
      fonte: "DIOPS/ANS (Documento de Informações Periódicas das Operadoras)",
      periodicidade: "Trimestral",
      unidade: "Reais (R$) e Porcentagem (%)",
      metodologia: "Sinistralidade = (Despesas com Eventos e Sinistros / Contraprestações Efetivas) * 100. Medida aditiva de fluxo calculada após a consolidação das somas do período.",
      observacoes: "Historicamente, o patamar prudencial de referência do setor oscila em torno de 80% a 85%.",
    },
    demandas: {
      titulo: "Demandas de Consumidores e Resolutividade NIP",
      definicao: "Notificações de Intermediação Preliminar (NIP) abertas por consumidores nos canais oficiais de atendimento da ANS.",
      fonte: "NIP/ANS (Sistema de Notificação de Intermediação Preliminar)",
      periodicidade: "Mensal",
      unidade: "Demandas e Taxa por 10.000 beneficiários",
      metodologia: "Taxa de demandas normalizada por 10 mil vidas. Resolutividade (%) = (Demandas voluntariamente resolvidas pela operadora / Total concluído) * 100.",
      observacoes: "A NIP permite sanar pendências assistenciais em prazo célere antes de processos sancionadores.",
    },
    geografia: {
      titulo: "Distribuição Geográfica e Taxa de Cobertura",
      definicao: "Alocação de beneficiários por Unidade da Federação e nível de penetração na população residente.",
      fonte: "SIB/ANS e Estimativas Populacionais do IBGE",
      periodicidade: "Anual (IBGE) / Mensal (SIB)",
      unidade: "Vidas e Porcentagem da População (%)",
      metodologia: "Taxa de Cobertura = (Total de Beneficiários Residentes na UF / População IBGE da UF) * 100.",
      observacoes: "Considera a UF de residência do beneficiário declarada pela operadora no SIB.",
    },
    perfil: {
      titulo: "Segmentação Assistencial e Tipo de Contratação",
      definicao: "Classificação regulatória dos contratos segundo a Lei nº 9.656/1998 e Resolução Normativa nº 63/2003.",
      fonte: "RPS/ANS e SIB/ANS",
      periodicidade: "Mensal",
      unidade: "Porcentagem e Vidas",
      metodologia: "Decomposição proporcional de contratos: Coletivo Empresarial, Individual/Familiar e Coletivo por Adesão.",
      observacoes: "Planos empresariais respondem por cerca de 70% do mercado médico-hospitalar nacional.",
    },
  };

  let activeInfo = $derived(
    $analyticalStore.activeDrawer
      ? METADATA_DICTIONARY[$analyticalStore.activeDrawer] ?? METADATA_DICTIONARY.geral
      : null
  );

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      analyticalStore.closeMetadata();
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if $analyticalStore.activeDrawer && activeInfo}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="drawer-overlay" onclick={() => analyticalStore.closeMetadata()}>
    <div
      class="drawer-panel"
      role="dialog"
      aria-modal="true"
      aria-labelledby="drawer-title"
      tabindex="-1"
      onclick={(e) => e.stopPropagation()}
    >
      <div class="drawer-header">
        <div>
          <span class="drawer-badge">Metadados & Governança de Dados</span>
          <h2 id="drawer-title" class="drawer-title">{activeInfo.titulo}</h2>
        </div>
        <button
          type="button"
          class="btn-close"
          onclick={() => analyticalStore.closeMetadata()}
          aria-label="Fechar"
        >
          ✕
        </button>
      </div>

      <div class="drawer-body">
        <div class="meta-row">
          <span class="meta-label">Definição:</span>
          <p class="meta-desc">{activeInfo.definicao}</p>
        </div>

        <div class="meta-grid">
          <div class="meta-box">
            <span class="meta-label">Fonte de Dados</span>
            <span class="meta-val">{activeInfo.fonte}</span>
          </div>
          <div class="meta-box">
            <span class="meta-label">Periodicidade</span>
            <span class="meta-val">{activeInfo.periodicidade}</span>
          </div>
          <div class="meta-box">
            <span class="meta-label">Unidade de Medida</span>
            <span class="meta-val">{activeInfo.unidade}</span>
          </div>
        </div>

        <div class="meta-row">
          <span class="meta-label">Metodologia e Regras de Agregação:</span>
          <p class="meta-desc">{activeInfo.metodologia}</p>
        </div>

        <div class="meta-row">
          <span class="meta-label">Observações Regulatórias e Notas:</span>
          <p class="meta-desc alert-box">{activeInfo.observacoes}</p>
        </div>
      </div>

      <div class="drawer-footer">
        <button
          type="button"
          class="btn-footer-close"
          onclick={() => analyticalStore.closeMetadata()}
        >
          Fechar
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .drawer-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(4px);
    z-index: 100;
    display: flex;
    justify-content: flex-end;
  }

  .drawer-panel {
    background: #ffffff;
    width: 100%;
    max-width: 520px;
    height: 100%;
    box-shadow: -4px 0 24px rgba(0, 0, 0, 0.15);
    display: flex;
    flex-direction: column;
    animation: slideIn 0.2s ease-out;
  }

  @keyframes slideIn {
    from {
      transform: translateX(100%);
    }
    to {
      transform: translateX(0);
    }
  }

  .drawer-header {
    padding: 1.5rem;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .drawer-badge {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #2563eb;
    margin-bottom: 0.35rem;
    display: block;
  }

  .drawer-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
    line-height: 1.3;
  }

  .btn-close {
    background: #f1f5f9;
    border: none;
    font-size: 0.875rem;
    color: #64748b;
    width: 32px;
    height: 32px;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;
  }

  .btn-close:hover {
    background: #e2e8f0;
    color: #0f172a;
  }

  .drawer-body {
    padding: 1.5rem;
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .meta-row {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .meta-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
  }

  .meta-desc {
    font-size: 0.875rem;
    color: #1e293b;
    line-height: 1.5;
    margin: 0;
  }

  .meta-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 0.75rem;
    margin: 0.5rem 0;
  }

  .meta-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .meta-val {
    font-size: 0.8125rem;
    font-weight: 600;
    color: #0f172a;
  }

  .alert-box {
    background: #f0fdf4;
    border-left: 3px solid #16a34a;
    padding: 0.75rem 1rem;
    border-radius: 0 6px 6px 0;
    color: #166534;
  }

  .drawer-footer {
    padding: 1rem 1.5rem;
    border-top: 1px solid #e2e8f0;
    display: flex;
    justify-content: flex-end;
  }

  .btn-footer-close {
    background: #2563eb;
    color: #ffffff;
    border: none;
    padding: 0.5rem 1.25rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
  }

  .btn-footer-close:hover {
    background: #1d4ed8;
  }
</style>
