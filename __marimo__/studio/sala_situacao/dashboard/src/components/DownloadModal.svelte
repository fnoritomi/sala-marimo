<script lang="ts">
  import { analyticalStore } from "../stores/analyticalStore";

  interface Props {
    payloadData?: any;
  }

  let { payloadData }: Props = $props();

  let selectedFormat = $state<"csv" | "json">("csv");
  let isDownloading = $state(false);

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      analyticalStore.setDownloadOpen(false);
    }
  }

  function triggerDownload() {
    isDownloading = true;

    try {
      const geo = payloadData?.geographic ?? [];
      const currentUf = $analyticalStore.selectedUf;
      const dataToExport = currentUf ? geo.filter((d: any) => d.sigla_uf === currentUf) : geo;

      let blob: Blob;
      let filename = `ans_sala_situacao_${currentUf ?? "brasil"}_${new Date().toISOString().slice(0, 10)}`;

      if (selectedFormat === "csv") {
        const headers = ["sigla_uf", "nome_uf", "regiao", "populacao", "vidas", "taxa_cobertura"];
        const rows = dataToExport.map((d: any) =>
          [d.sigla_uf, `"${d.nome_uf}"`, `"${d.regiao}"`, d.populacao, d.vidas, d.taxa_cobertura].join(";")
        );
        const csvContent = "\uFEFF" + [headers.join(";"), ...rows].join("\n");
        blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        filename += ".csv";
      } else {
        const jsonContent = JSON.stringify(payloadData, null, 2);
        blob = new Blob([jsonContent], { type: "application/json" });
        filename += ".json";
      }

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setTimeout(() => {
        isDownloading = false;
        analyticalStore.setDownloadOpen(false);
      }, 400);
    } catch (err) {
      console.error("Erro ao gerar download:", err);
      isDownloading = false;
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if $analyticalStore.isDownloadOpen}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="modal-overlay" onclick={() => analyticalStore.setDownloadOpen(false)}>
    <div
      class="modal-panel"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      tabindex="-1"
      onclick={(e) => e.stopPropagation()}
    >
      <div class="modal-header">
        <h3 id="modal-title" class="modal-title">Exportação de Dados Analíticos</h3>
        <button
          type="button"
          class="btn-close"
          onclick={() => analyticalStore.setDownloadOpen(false)}
        >
          ✕
        </button>
      </div>

      <div class="modal-body">
        <p class="modal-desc">
          Exporte os dados consolidados do setor respeitando os filtros e recortes atualmente ativos na interface.
        </p>

        <div class="filter-summary-box">
          <span class="summary-label">Recorte selecionado para exportação:</span>
          <ul class="summary-list">
            <li><strong>UF:</strong> {$analyticalStore.selectedUf ?? "Brasil (Consolidado Nacional)"}</li>
            <li><strong>Assistência:</strong> {$analyticalStore.assistencia ?? "Todas as Coberturas"}</li>
            <li><strong>Contratação:</strong> {$analyticalStore.contratacao ?? "Todas as Contratações"}</li>
            <li><strong>Modalidade:</strong> {$analyticalStore.modalidade ?? "Todas as Modalidades"}</li>
          </ul>
        </div>

        <div class="format-selection">
          <span class="summary-label">Escolha o formato do arquivo:</span>
          <div class="radio-options">
            <label class="format-card {selectedFormat === 'csv' ? 'selected' : ''}">
              <input
                type="radio"
                name="format"
                value="csv"
                checked={selectedFormat === "csv"}
                onchange={() => (selectedFormat = "csv")}
              />
              <div class="format-info">
                <strong>CSV Tabular (Excel / BI)</strong>
                <span>Compatível com Excel, PowerBI e Python (separador ponto-e-vírgula com BOM UTF-8)</span>
              </div>
            </label>

            <label class="format-card {selectedFormat === 'json' ? 'selected' : ''}">
              <input
                type="radio"
                name="format"
                value="json"
                checked={selectedFormat === "json"}
                onchange={() => (selectedFormat = "json")}
              />
              <div class="format-info">
                <strong>JSON Estruturado</strong>
                <span>Pacote completo de séries históricas, KPIs e distribuições para integração de API</span>
              </div>
            </label>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button
          type="button"
          class="btn-cancel"
          onclick={() => analyticalStore.setDownloadOpen(false)}
        >
          Cancelar
        </button>
        <button
          type="button"
          class="btn-confirm"
          onclick={triggerDownload}
          disabled={isDownloading}
        >
          {isDownloading ? "Gerando arquivo..." : "Iniciar Download"}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(4px);
    z-index: 110;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }

  .modal-panel {
    background: #ffffff;
    border-radius: 12px;
    width: 100%;
    max-width: 520px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
    overflow: hidden;
    animation: scaleIn 0.15s ease-out;
  }

  @keyframes scaleIn {
    from {
      opacity: 0;
      transform: scale(0.95);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }

  .modal-header {
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .modal-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
  }

  .btn-close {
    background: #f1f5f9;
    border: none;
    font-size: 0.8125rem;
    color: #64748b;
    width: 28px;
    height: 28px;
    border-radius: 6px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .modal-body {
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .modal-desc {
    font-size: 0.875rem;
    color: #475569;
    margin: 0;
    line-height: 1.5;
  }

  .filter-summary-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.875rem 1rem;
  }

  .summary-label {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #475569;
    display: block;
    margin-bottom: 0.4rem;
  }

  .summary-list {
    margin: 0;
    padding-left: 1.2rem;
    font-size: 0.8125rem;
    color: #1e293b;
    line-height: 1.6;
  }

  .format-selection {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .radio-options {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }

  .format-card {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 0.875rem;
    cursor: pointer;
    transition: all 0.15s;
  }

  .format-card:hover {
    background: #f8fafc;
  }

  .format-card.selected {
    border-color: #2563eb;
    background: #eff6ff;
  }

  .format-info {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .format-info strong {
    font-size: 0.875rem;
    color: #0f172a;
  }

  .format-info span {
    font-size: 0.75rem;
    color: #64748b;
  }

  .modal-footer {
    padding: 1rem 1.5rem;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
  }

  .btn-cancel {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    color: #475569;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
  }

  .btn-confirm {
    background: #2563eb;
    color: #ffffff;
    border: 1px solid #1d4ed8;
    padding: 0.5rem 1.25rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
  }

  .btn-confirm:hover {
    background: #1d4ed8;
  }
</style>
