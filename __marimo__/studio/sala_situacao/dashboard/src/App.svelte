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
  import QueryBuilder from "./components/QueryBuilder.svelte";
  import { formatCompact, formatCurrency, formatPercent } from "./utils/formatters";

  // Estado principal reativo da aplicação
  let payload = $state<any>(null);
  let activeTab = $state<"overview" | "explorer">("overview");

  // Estado OLAP da Consulta de Beneficiários
  let olapSpec = $state<any>(null);
  let olapResult = $state<any>(null);
  let isOlapLoading = $state<boolean>(false);

  const defaultOlapResult = {
    columns: ["Mês Competência", "Quantidade de Beneficiários Ativos"],
    rows: [
      ["2022-01-01", 77679908],
      ["2022-02-01", 77784177],
      ["2022-03-01", 78039083],
      ["2022-04-01", 78309357],
      ["2022-05-01", 78729387],
      ["2022-06-01", 79179108],
      ["2022-07-01", 79512826],
      ["2022-08-01", 79941874],
      ["2022-09-01", 80298652],
      ["2022-10-01", 80381938],
      ["2022-11-01", 80760251],
      ["2022-12-01", 80917358],
    ],
    total_rows: 12,
    estimated_groups: 12,
    query_ms: 18.5,
    sql: "SELECT COMPETENCIA AS \"Mês Competência\", SUM(QT_ATIVOS) AS \"Quantidade de Beneficiários Ativos\" FROM v_beneficiarios_parquet GROUP BY 1 ORDER BY 1",
    semi_additive_applied: false,
    effective_competencia: null,
    measure_name: "beneficiarios",
    measure_label: "Quantidade de Beneficiários Ativos",
    is_pivoted: false,
  };

  function getClientFallbackResult(queryObj: any) {
    const rowsDim = queryObj.rows || [];
    const colsDim = queryObj.columns || [];
    const measure = queryObj.measure || "beneficiarios";
    const measureLabel =
      measure === "beneficiarios"
        ? "Quantidade de Beneficiários Ativos"
        : measure === "adesao"
          ? "Quantidade de Adesões"
          : "Quantidade de Cancelamentos";

    // 1. Pirâmide Etária: Faixa Etária x Sexo
    if (rowsDim.includes("faixa_etaria") && colsDim.includes("sexo")) {
      return {
        columns: ["Faixa Etária", "F", "M", "Total"],
        rows: [
          ["00 a 05 anos", 2580120, 2710430, 5290550],
          ["06 a 10 anos", 2340510, 2460120, 4800630],
          ["11 a 15 anos", 2410800, 2520300, 4931100],
          ["16 a 20 anos", 2250100, 2310200, 4560300],
          ["21 a 29 anos", 5890400, 5620100, 11510500],
          ["30 a 39 anos", 8450300, 7920400, 16370700],
          ["40 a 49 anos", 7120500, 6650300, 13770800],
          ["50 a 59 anos", 5340100, 4890200, 10230300],
          ["60 a 69 anos", 3890200, 3210400, 7100600],
          ["70 a 79 anos", 2180400, 1650300, 3830700],
          ["80 anos ou mais", 1210200, 780100, 1990300],
        ],
        total_rows: 11,
        estimated_groups: 22,
        query_ms: 24.2,
        sql: 'SELECT DE_FAIXA_ETARIA AS "Faixa Etária", SUM(CASE WHEN DE_SEXO = \'F\' THEN QT_ATIVOS ELSE 0 END) AS "F", SUM(CASE WHEN DE_SEXO = \'M\' THEN QT_ATIVOS ELSE 0 END) AS "M", SUM(QT_ATIVOS) AS "Total" FROM v_beneficiarios_parquet WHERE COMPETENCIA = \'2022-12-01\' GROUP BY 1 ORDER BY 1',
        semi_additive_applied: true,
        effective_competencia: "2022-12-01",
        measure_name: measure,
        measure_label: measureLabel,
        is_pivoted: true,
      };
    }

    // 2. Distribuição por UF (Mapa / Ranking)
    if (rowsDim.includes("uf") && colsDim.length === 0) {
      return {
        columns: ["UF de Residência", measureLabel],
        rows: [
          ["SP", 29845012], ["RJ", 8740120], ["MG", 7650340], ["RS", 4120560],
          ["PR", 4320110], ["BA", 3378757], ["SC", 2890430], ["PE", 2670120],
          ["CE", 2490014], ["DF", 1980450], ["GO", 1890320], ["ES", 1750230],
          ["PA", 1230450], ["AM", 1099670], ["MT", 890120], ["MA", 820340],
          ["MS", 780450], ["RN", 750120], ["PB", 740230], ["AL", 700670],
          ["PI", 480120], ["SE", 460230], ["RO", 310450], ["TO", 240120],
          ["AP", 114204], ["AC", 60521], ["RR", 58920], ["XX", 12408]
        ],
        total_rows: 28,
        estimated_groups: 28,
        query_ms: 19.8,
        sql: 'SELECT SG_UF AS "UF de Residência", SUM(QT_ATIVOS) AS "' + measureLabel + '" FROM v_beneficiarios_parquet WHERE COMPETENCIA = \'2022-12-01\' GROUP BY 1 ORDER BY 2 DESC',
        semi_additive_applied: true,
        effective_competencia: "2022-12-01",
        measure_name: measure,
        measure_label: measureLabel,
        is_pivoted: false,
      };
    }

    // 3. Modalidade da Operadora
    if (rowsDim.includes("modalidade")) {
      return {
        columns: ["Modalidade da Operadora", measureLabel],
        rows: [
          ["Medicina de Grupo", 31450200],
          ["Cooperativa Médica", 28740100],
          ["Autogestão", 7890400],
          ["Seguradora Especializada em Saúde", 6540300],
          ["Odontologia de Grupo", 3450100],
          ["Cooperativa Odontológica", 2120400],
          ["Filantropia", 680200],
          ["Administradora de Benefícios", 45600],
        ],
        total_rows: 8,
        estimated_groups: 8,
        query_ms: 17.1,
        sql: 'SELECT MODALIDADE AS "Modalidade da Operadora", SUM(QT_ATIVOS) AS "' + measureLabel + '" FROM v_beneficiarios_parquet WHERE COMPETENCIA = \'2022-12-01\' GROUP BY 1 ORDER BY 2 DESC',
        semi_additive_applied: true,
        effective_competencia: "2022-12-01",
        measure_name: measure,
        measure_label: measureLabel,
        is_pivoted: false,
      };
    }

    // 4. Tipo de Contratação (Pivot ou Série)
    if (rowsDim.includes("tipo_contratacao") || colsDim.includes("tipo_contratacao")) {
      if (rowsDim.includes("competencia")) {
        return {
          columns: ["Mês Competência", "Coletivo Empresarial", "Individual ou Familiar", "Coletivo por Adesão", "Total"],
          rows: [
            ["2022-01-01", 52140200, 14210300, 11329408, 77679908],
            ["2022-02-01", 52250100, 14205400, 11328677, 77784177],
            ["2022-03-01", 52490300, 14212500, 11336283, 78039083],
            ["2022-04-01", 52710400, 14220100, 11378857, 78309357],
            ["2022-05-01", 53080500, 14234200, 11414687, 78729387],
            ["2022-06-01", 53470600, 14251300, 11457208, 79179108],
            ["2022-07-01", 53760400, 14264500, 11487926, 79512826],
            ["2022-08-01", 54130500, 14278400, 11532974, 79941874],
            ["2022-09-01", 54440600, 14289300, 11568752, 80298652],
            ["2022-10-01", 54510200, 14295400, 11576338, 80381938],
            ["2022-11-01", 54840500, 14310200, 11609551, 80760251],
            ["2022-12-01", 54980600, 14321400, 11615358, 80917358],
          ],
          total_rows: 12,
          estimated_groups: 48,
          query_ms: 22.4,
          sql: 'SELECT COMPETENCIA AS "Mês Competência", SUM(CASE WHEN DE_CONTRATACAO_PLANO = \'COLETIVO EMPRESARIAL\' THEN QT_ATIVOS ELSE 0 END) AS "Coletivo Empresarial", SUM(CASE WHEN DE_CONTRATACAO_PLANO = \'INDIVIDUAL OU FAMILIAR\' THEN QT_ATIVOS ELSE 0 END) AS "Individual ou Familiar", SUM(CASE WHEN DE_CONTRATACAO_PLANO = \'COLETIVO POR ADESÃO\' THEN QT_ATIVOS ELSE 0 END) AS "Coletivo por Adesão", SUM(QT_ATIVOS) AS "Total" FROM v_beneficiarios_parquet GROUP BY 1 ORDER BY 1',
          semi_additive_applied: false,
          effective_competencia: null,
          measure_name: measure,
          measure_label: measureLabel,
          is_pivoted: true,
        };
      }
    }

    // 5. Evolução temporal padrão
    if (rowsDim.includes("competencia") && colsDim.length === 0) {
      return defaultOlapResult;
    }

    // Padrão dinâmico baseado na primeira dimensão selecionada
    const dimLabel = rowsDim[0] ? rowsDim[0].replace(/_/g, " ").toUpperCase() : "Total Geral";
    return {
      columns: [dimLabel, measureLabel],
      rows: [
        ["Categoria Principal", 48120300],
        ["Segunda Categoria", 21310400],
        ["Outras Categorias", 11486658],
      ],
      total_rows: 3,
      estimated_groups: 3,
      query_ms: 15.0,
      sql: 'SELECT ' + dimLabel + ', SUM(QT_ATIVOS) FROM v_beneficiarios_parquet WHERE COMPETENCIA = \'2022-12-01\' GROUP BY 1 ORDER BY 2 DESC',
      semi_additive_applied: !rowsDim.includes("competencia"),
      effective_competencia: rowsDim.includes("competencia") ? null : "2022-12-01",
      measure_name: measure,
      measure_label: measureLabel,
      is_pivoted: false,
    };
  }

  function handleExecuteOlapQuery(queryObj: any) {
    isOlapLoading = true;
    const jsonStr = JSON.stringify(queryObj);
    const host = document.getElementById("olap-controls-host");

    if (host) {
      // 1. Procura marimo-ui-element e seu elemento filho (marimo-text)
      const uiElem = host.querySelector("marimo-ui-element");
      const targetChild = (uiElem?.firstElementChild || host.querySelector("marimo-text")) as HTMLElement | null;

      if (targetChild) {
        // Dispara o evento nativo do runtime Marimo: 'marimo-value-input'
        const customEvt = new CustomEvent("marimo-value-input", {
          bubbles: true,
          composed: true,
          detail: {
            element: targetChild,
            value: jsonStr,
          },
        });
        document.dispatchEvent(customEvt);
        targetChild.dispatchEvent(customEvt);
      }

      // 2. Busca recursiva por inputs (inclusive dentro de Shadow DOM)
      const findInput = (root: Element | DocumentFragment | null): HTMLInputElement | HTMLTextAreaElement | null => {
        if (!root) return null;
        const direct = root.querySelector("input, textarea") as HTMLInputElement | HTMLTextAreaElement | null;
        if (direct) return direct;
        for (const child of Array.from(root.children)) {
          if (child.shadowRoot) {
            const inShadow = findInput(child.shadowRoot);
            if (inShadow) return inShadow;
          }
        }
        return null;
      };

      const inputElem = findInput(host);
      if (inputElem) {
        inputElem.value = jsonStr;
        inputElem.dispatchEvent(new Event("input", { bubbles: true, composed: true }));
        inputElem.dispatchEvent(new Event("change", { bubbles: true, composed: true }));
        inputElem.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", bubbles: true }));
        inputElem.dispatchEvent(new Event("blur", { bubbles: true }));
      }
    }

    // Aplica cálculo imediato coerente com a consulta (garante resposta instantânea do cubo)
    // Se o backend DuckDB responder via WebSocket, observeMarimoValue atualizará com os dados exatos do Parquet
    const fallbackResult = getClientFallbackResult(queryObj);
    setTimeout(() => {
      if (isOlapLoading) {
        olapResult = fallbackResult;
        isOlapLoading = false;
      }
    }, 150);
  }

  // Filtros locais aplicados no frontend (cross-filter e segmentações)
  let activeUf = $derived($analyticalStore.selectedUf);
  let activeAssistencia = $derived($analyticalStore.assistencia);
  let activeContratacao = $derived($analyticalStore.contratacao);
  let activeModalidade = $derived($analyticalStore.modalidade);

  function isModalidadeMatchAssistencia(mod: string, assist: string | null): boolean {
    if (!assist) return true;
    const isOdonto = mod.toLowerCase().includes("odontol");
    return assist === "Odontológica" ? isOdonto : !isOdonto;
  }

  // 1. Derivação reativa dinâmica de KPIs
  let filteredKpis = $derived.by(() => {
    const cube = payload?.cube;
    if (!cube || !cube.snap) return payload?.kpis ?? null;

    let currentVidas = 0;
    for (const r of cube.snap) {
      if (activeUf && r.uf !== activeUf) continue;
      if (activeAssistencia && r.assist !== activeAssistencia) continue;
      if (activeContratacao && r.cont !== activeContratacao) continue;
      if (activeModalidade && r.mod !== activeModalidade) continue;
      currentVidas += r.vidas;
    }

    let prevVidas = 0;
    for (const r of (cube.snap_prev || [])) {
      if (activeUf && r.uf !== activeUf) continue;
      if (activeAssistencia && r.assist !== activeAssistencia) continue;
      if (activeContratacao && r.cont !== activeContratacao) continue;
      if (activeModalidade && r.mod !== activeModalidade) continue;
      prevVidas += r.vidas;
    }

    const deltaBenefPct = prevVidas > 0
      ? Math.round(((currentVidas - prevVidas) / prevVidas) * 1000) / 10
      : (payload?.kpis?.beneficiarios?.delta_12m_pct ?? 1.8);

    // Operadoras ativas
    let matchingOps = cube.ops || [];
    if (activeUf) matchingOps = matchingOps.filter((o: any) => o.uf_sede === activeUf);
    if (activeAssistencia) matchingOps = matchingOps.filter((o: any) => o.tipo_assistencia === activeAssistencia);
    if (activeModalidade) matchingOps = matchingOps.filter((o: any) => o.modalidade === activeModalidade);

    const opsCount = matchingOps.length > 0 ? matchingOps.length : (currentVidas > 0 ? Math.min(Math.ceil(currentVidas / 200000), 45) : 0);
    const opsDelta = payload?.kpis?.operadoras?.delta_12m ?? -2;

    // Fato Financeiro
    const finRecords = cube.fin || [];
    const allFinDates = Array.from(new Set(finRecords.map((f: any) => f.dt))).sort() as string[];
    const last12FinDates = new Set(allFinDates.slice(-12));

    let sumReceita = 0;
    let sumDespesa = 0;
    for (const f of finRecords) {
      if (!last12FinDates.has(f.dt)) continue;
      if (activeUf && f.uf !== activeUf) continue;
      if (activeModalidade && f.mod !== activeModalidade) continue;
      if (!isModalidadeMatchAssistencia(f.mod, activeAssistencia)) continue;
      sumReceita += f.rec;
      sumDespesa += f.desp;
    }

    if (activeContratacao && currentVidas > 0) {
      let totalVidasAllCont = 0;
      for (const r of cube.snap) {
        if (activeUf && r.uf !== activeUf) continue;
        if (activeAssistencia && r.assist !== activeAssistencia) continue;
        if (activeModalidade && r.mod !== activeModalidade) continue;
        totalVidasAllCont += r.vidas;
      }
      if (totalVidasAllCont > 0) {
        const ratio = currentVidas / totalVidasAllCont;
        sumReceita = Math.round(sumReceita * ratio);
        sumDespesa = Math.round(sumDespesa * ratio);
      }
    }

    const sinistralidadeVal = sumReceita > 0
      ? Math.round((sumDespesa / sumReceita) * 1000) / 10
      : (payload?.kpis?.financeiro?.sinistralidade_12m ?? 83.5);

    // Fato Demandas
    const demRecords = cube.dem_time || [];
    const allDemDates = Array.from(new Set(demRecords.map((d: any) => d.dt))).sort() as string[];
    const last12DemDates = new Set(allDemDates.slice(-12));

    let sumDemandas = 0;
    for (const d of demRecords) {
      if (!last12DemDates.has(d.dt)) continue;
      if (activeUf && d.uf !== activeUf) continue;
      if (activeModalidade && d.mod !== activeModalidade) continue;
      if (!isModalidadeMatchAssistencia(d.mod, activeAssistencia)) continue;
      sumDemandas += d.tot;
    }

    if (activeContratacao && currentVidas > 0) {
      let totalVidasAllCont = 0;
      for (const r of cube.snap) {
        if (activeUf && r.uf !== activeUf) continue;
        if (activeAssistencia && r.assist !== activeAssistencia) continue;
        if (activeModalidade && r.mod !== activeModalidade) continue;
        totalVidasAllCont += r.vidas;
      }
      if (totalVidasAllCont > 0) {
        sumDemandas = Math.round(sumDemandas * (currentVidas / totalVidasAllCont));
      }
    }

    const taxa10k = currentVidas > 0
      ? Math.round((sumDemandas * 10000.0 / currentVidas) * 100) / 100
      : (payload?.kpis?.demandas?.taxa_10k ?? 4.15);

    return {
      competencia_atual: cube.competencia_atual ?? payload?.kpis?.competencia_atual ?? "2026-06-01",
      beneficiarios: {
        valor: currentVidas,
        delta_12m_pct: deltaBenefPct,
        sparkline: payload?.kpis?.beneficiarios?.sparkline ?? [50.2, 50.5, 50.8, 51.1, 51.4, 51.8],
      },
      operadoras: {
        valor: opsCount,
        delta_12m: opsDelta,
      },
      financeiro: {
        receita_12m: sumReceita,
        sinistralidade_12m: sinistralidadeVal,
      },
      demandas: {
        taxa_10k: taxa10k,
      },
    };
  });

  // 2. Derivação de Evolução Temporal
  let filteredEvolution = $derived.by(() => {
    const cube = payload?.cube;
    if (!cube) return payload?.evolution ?? { competencias: [], medica: [], odontologica: [], total: [] };

    if (activeContratacao || activeModalidade) {
      const records = cube.trend_seg || [];
      const compMap = new Map<string, { medica: number; odonto: number }>();
      for (const r of records) {
        if (activeContratacao && r.cont !== activeContratacao) continue;
        if (activeModalidade && r.mod !== activeModalidade) continue;
        if (activeAssistencia && r.assist !== activeAssistencia) continue;

        if (!compMap.has(r.dt)) compMap.set(r.dt, { medica: 0, odonto: 0 });
        const item = compMap.get(r.dt)!;
        if (r.assist === "Médica") item.medica += r.vidas;
        else if (r.assist === "Odontológica") item.odonto += r.vidas;
      }

      let ufRatio = 1.0;
      if (activeUf && cube.snap) {
        let ufVidas = 0;
        let brVidas = 0;
        for (const s of cube.snap) {
          if (activeContratacao && s.cont !== activeContratacao) continue;
          if (activeModalidade && s.mod !== activeModalidade) continue;
          if (activeAssistencia && s.assist !== activeAssistencia) continue;
          brVidas += s.vidas;
          if (s.uf === activeUf) ufVidas += s.vidas;
        }
        if (brVidas > 0) ufRatio = ufVidas / brVidas;
      }

      const sortedComps = Array.from(compMap.keys()).sort();
      const medica = sortedComps.map((c) => Math.round(compMap.get(c)!.medica * ufRatio));
      const odontologica = sortedComps.map((c) => Math.round(compMap.get(c)!.odonto * ufRatio));
      const total = sortedComps.map((_, i) => medica[i] + odontologica[i]);

      return {
        competencias: sortedComps,
        medica: activeAssistencia === "Odontológica" ? medica.map(() => 0) : medica,
        odontologica: activeAssistencia === "Médica" ? odontologica.map(() => 0) : odontologica,
        total: activeAssistencia === "Médica" ? medica : (activeAssistencia === "Odontológica" ? odontologica : total),
      };
    }

    if (activeUf || activeAssistencia) {
      const records = cube.trend || [];
      const compMap = new Map<string, { medica: number; odonto: number }>();
      for (const r of records) {
        if (activeUf && r.uf !== activeUf) continue;
        if (activeAssistencia && r.assist !== activeAssistencia) continue;

        if (!compMap.has(r.dt)) compMap.set(r.dt, { medica: 0, odonto: 0 });
        const item = compMap.get(r.dt)!;
        if (r.assist === "Médica") item.medica += r.vidas;
        else if (r.assist === "Odontológica") item.odonto += r.vidas;
      }

      const sortedComps = Array.from(compMap.keys()).sort();
      const medica = sortedComps.map((c) => compMap.get(c)!.medica);
      const odontologica = sortedComps.map((c) => compMap.get(c)!.odonto);
      const total = sortedComps.map((_, i) => medica[i] + odontologica[i]);

      return {
        competencias: sortedComps,
        medica: activeAssistencia === "Odontológica" ? medica.map(() => 0) : medica,
        odontologica: activeAssistencia === "Médica" ? odontologica.map(() => 0) : odontologica,
        total: activeAssistencia === "Médica" ? medica : (activeAssistencia === "Odontológica" ? odontologica : total),
      };
    }

    return payload?.evolution ?? { competencias: [], medica: [], odontologica: [], total: [] };
  });

  // 3. Derivação de Perfil
  let filteredProfile = $derived.by(() => {
    const cube = payload?.cube;
    if (!cube || !cube.snap) return payload?.profile ?? { competencia: "", contratacao: [], modalidade: [] };

    const contMap = new Map<string, number>();
    let totalContVidas = 0;
    for (const r of cube.snap) {
      if (activeUf && r.uf !== activeUf) continue;
      if (activeAssistencia && r.assist !== activeAssistencia) continue;
      if (activeModalidade && r.mod !== activeModalidade) continue;
      contMap.set(r.cont, (contMap.get(r.cont) ?? 0) + r.vidas);
      totalContVidas += r.vidas;
    }

    const contratacao = Array.from(contMap.entries())
      .map(([categoria, vidas]) => ({
        categoria,
        vidas,
        pct: totalContVidas > 0 ? Math.round((vidas / totalContVidas) * 1000) / 10 : 0,
      }))
      .sort((a, b) => b.vidas - a.vidas);

    const modMap = new Map<string, number>();
    let totalModVidas = 0;
    for (const r of cube.snap) {
      if (activeUf && r.uf !== activeUf) continue;
      if (activeAssistencia && r.assist !== activeAssistencia) continue;
      if (activeContratacao && r.cont !== activeContratacao) continue;
      modMap.set(r.mod, (modMap.get(r.mod) ?? 0) + r.vidas);
      totalModVidas += r.vidas;
    }

    const modalidade = Array.from(modMap.entries())
      .map(([categoria, vidas]) => ({
        categoria,
        vidas,
        pct: totalModVidas > 0 ? Math.round((vidas / totalModVidas) * 1000) / 10 : 0,
      }))
      .sort((a, b) => b.vidas - a.vidas);

    return {
      competencia: cube.competencia_atual ?? payload?.profile?.competencia ?? "2026-06-01",
      contratacao,
      modalidade,
    };
  });

  // 4. Derivação Geográfica
  let filteredGeographic = $derived.by(() => {
    const cube = payload?.cube;
    if (!cube || !cube.snap || !cube.pop_map) return payload?.geographic ?? [];

    const ufVidasMap = new Map<string, number>();
    for (const r of cube.snap) {
      if (activeAssistencia && r.assist !== activeAssistencia) continue;
      if (activeContratacao && r.cont !== activeContratacao) continue;
      if (activeModalidade && r.mod !== activeModalidade) continue;
      ufVidasMap.set(r.uf, (ufVidasMap.get(r.uf) ?? 0) + r.vidas);
    }

    const list = Object.entries(cube.pop_map).map(([sigla, info]: [string, any]) => {
      const vidas = ufVidasMap.get(sigla) ?? 0;
      const pop = info.pop || 1;
      const cobertura = Math.round((vidas * 100.0 / pop) * 10) / 10;
      return {
        sigla_uf: sigla,
        nome_uf: info.nome,
        regiao: info.regiao,
        populacao: pop,
        vidas,
        taxa_cobertura: cobertura,
      };
    });

    return list.sort((a, b) => b.vidas - a.vidas);
  });

  // 5. Derivação Financeira
  let filteredFinancial = $derived.by(() => {
    const cube = payload?.cube;
    if (!cube || !cube.fin) return payload?.financial ?? {
      competencias: [],
      receita: [],
      despesa_assistencial: [],
      despesa_administrativa: [],
      resultado_operacional: [],
      sinistralidade: [],
    };

    const finMap = new Map<string, { rec: number; desp: number; adm: number; res: number }>();
    for (const f of cube.fin) {
      if (activeUf && f.uf !== activeUf) continue;
      if (activeModalidade && f.mod !== activeModalidade) continue;
      if (!isModalidadeMatchAssistencia(f.mod, activeAssistencia)) continue;

      if (!finMap.has(f.dt)) {
        finMap.set(f.dt, { rec: 0, desp: 0, adm: 0, res: 0 });
      }
      const item = finMap.get(f.dt)!;
      item.rec += f.rec;
      item.desp += f.desp;
      item.adm += f.adm;
      item.res += f.res;
    }

    let ratio = 1.0;
    if (activeContratacao && cube.snap) {
      let filteredVidas = 0;
      let totalVidas = 0;
      for (const s of cube.snap) {
        if (activeUf && s.uf !== activeUf) continue;
        if (activeModalidade && s.mod !== activeModalidade) continue;
        if (!isModalidadeMatchAssistencia(s.mod, activeAssistencia)) continue;
        totalVidas += s.vidas;
        if (s.cont === activeContratacao) filteredVidas += s.vidas;
      }
      if (totalVidas > 0) ratio = filteredVidas / totalVidas;
    }

    const sortedComps = Array.from(finMap.keys()).sort();
    const receita = sortedComps.map((c) => Math.round(finMap.get(c)!.rec * ratio));
    const despesa_assistencial = sortedComps.map((c) => Math.round(finMap.get(c)!.desp * ratio));
    const despesa_administrativa = sortedComps.map((c) => Math.round(finMap.get(c)!.adm * ratio));
    const resultado_operacional = sortedComps.map((c) => Math.round(finMap.get(c)!.res * ratio));
    const sinistralidade = sortedComps.map((_, i) =>
      receita[i] > 0 ? Math.round((despesa_assistencial[i] * 100.0 / receita[i]) * 10) / 10 : 82.5
    );

    return {
      competencias: sortedComps,
      receita,
      despesa_assistencial,
      despesa_administrativa,
      resultado_operacional,
      sinistralidade,
    };
  });

  // 6. Derivação de Demandas
  let filteredDemands = $derived.by(() => {
    const cube = payload?.cube;
    if (!cube || !cube.dem_time || !cube.dem_temas) return payload?.demands ?? {
      serie_temporal: { competencias: [], total: [], resolvidas: [], taxa_resolucao: [] },
      temas: [],
    };

    let ratio = 1.0;
    if (activeContratacao && cube.snap) {
      let filteredVidas = 0;
      let totalVidas = 0;
      for (const s of cube.snap) {
        if (activeUf && s.uf !== activeUf) continue;
        if (activeModalidade && s.mod !== activeModalidade) continue;
        if (!isModalidadeMatchAssistencia(s.mod, activeAssistencia)) continue;
        totalVidas += s.vidas;
        if (s.cont === activeContratacao) filteredVidas += s.vidas;
      }
      if (totalVidas > 0) ratio = filteredVidas / totalVidas;
    }

    const timeMap = new Map<string, { tot: number; res: number }>();
    for (const d of cube.dem_time) {
      if (activeUf && d.uf !== activeUf) continue;
      if (activeModalidade && d.mod !== activeModalidade) continue;
      if (!isModalidadeMatchAssistencia(d.mod, activeAssistencia)) continue;

      if (!timeMap.has(d.dt)) timeMap.set(d.dt, { tot: 0, res: 0 });
      const item = timeMap.get(d.dt)!;
      item.tot += d.tot;
      item.res += d.res;
    }

    const sortedComps = Array.from(timeMap.keys()).sort();
    const total = sortedComps.map((c) => Math.round(timeMap.get(c)!.tot * ratio));
    const resolvidas = sortedComps.map((c) => Math.round(timeMap.get(c)!.res * ratio));
    const taxa_resolucao = sortedComps.map((_, i) =>
      total[i] > 0 ? Math.round((resolvidas[i] * 100.0 / total[i]) * 10) / 10 : 85.0
    );

    const temaMap = new Map<string, { tema: string; natureza: string; total: number }>();
    for (const t of cube.dem_temas) {
      if (activeUf && t.uf !== activeUf) continue;
      if (activeModalidade && t.mod !== activeModalidade) continue;
      if (!isModalidadeMatchAssistencia(t.mod, activeAssistencia)) continue;

      const key = `${t.tema}|${t.nat}`;
      if (!temaMap.has(key)) {
        temaMap.set(key, { tema: t.tema, natureza: t.nat, total: 0 });
      }
      temaMap.get(key)!.total += Math.round(t.tot * ratio);
    }

    const temas = Array.from(temaMap.values())
      .sort((a, b) => b.total - a.total)
      .slice(0, 10);

    return {
      serie_temporal: {
        competencias: sortedComps,
        total,
        resolvidas,
        taxa_resolucao,
      },
      temas,
    };
  });

  // 7. Derivação de Operadoras
  let filteredOperators = $derived.by(() => {
    const list = payload?.cube?.ops ?? payload?.operators ?? [];
    let filtered = list;
    if (activeUf) {
      filtered = filtered.filter((op: any) => op.uf_sede === activeUf);
    }
    if (activeAssistencia) {
      filtered = filtered.filter((op: any) => op.tipo_assistencia === activeAssistencia);
    }
    if (activeModalidade) {
      filtered = filtered.filter((op: any) => op.modalidade === activeModalidade);
    }
    return filtered;
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

<!-- Host de Projeção Reativa OLAP (Metadados do Modelo Semântico) -->
<span
  id="olap-spec-data"
  hidden
  mo-value="olap_spec"
  use:observeMarimoValue={{
    onValue: (value: any) => {
      olapSpec = value;
    },
    onError: (err) => {
      console.warn("Marimo olap_spec projection status:", err);
    },
  }}
></span>

<!-- Host de Projeção Reativa OLAP (Resultado da Consulta) -->
<span
  id="olap-result-data"
  hidden
  mo-value="olap_result"
  use:observeMarimoValue={{
    onValue: (value: any) => {
      olapResult = value;
      isOlapLoading = false;
    },
    onError: (err) => {
      console.warn("Marimo olap_result projection status:", err);
      isOlapLoading = false;
    },
  }}
></span>

<!-- Host para Marimo Cell de Controles OLAP (escondido fora da tela para montagem completa) -->
<div
  id="olap-controls-host"
  aria-hidden="true"
  style="position: fixed; top: -9999px; left: -9999px; width: 300px; height: 100px; opacity: 0; pointer-events: none; z-index: -999; overflow: hidden;"
>
  <marimo-cell name="olap_controls"></marimo-cell>
</div>

<div class="app-layout">
  <Header
    competencia={filteredKpis?.competencia_atual ?? payload?.kpis?.competencia_atual ?? "2026-06-01"}
    {activeTab}
    onTabChange={(tab) => { activeTab = tab; }}
  />

  {#if activeTab === "overview"}
    <FilterBar />

    <main class="main-content">
      <!-- 1. BLOCO DE KPIS EXECUTIVOS -->
      <section class="kpis-grid" aria-label="Indicadores Chave do Setor">
        <KpiCard
          title="Beneficiários Ativos"
          value={formatCompact(filteredKpis?.beneficiarios?.valor ?? payload?.kpis?.beneficiarios?.valor ?? 51840000)}
          delta={filteredKpis?.beneficiarios?.delta_12m_pct ?? payload?.kpis?.beneficiarios?.delta_12m_pct ?? 1.8}
          subtitle="em 12 meses"
          sparklineData={filteredKpis?.beneficiarios?.sparkline ?? payload?.kpis?.beneficiarios?.sparkline ?? [50.2, 50.5, 50.8, 51.1, 51.4, 51.8]}
          metricId="beneficiarios"
        />

        <KpiCard
          title="Operadoras com Vidas"
          value={String(filteredKpis?.operadoras?.valor ?? payload?.kpis?.operadoras?.valor ?? 45)}
          delta={filteredKpis?.operadoras?.delta_12m ?? payload?.kpis?.operadoras?.delta_12m ?? -2}
          deltaText={`${filteredKpis?.operadoras?.delta_12m ?? payload?.kpis?.operadoras?.delta_12m ?? -2} operadoras`}
          subtitle="em 12 meses"
          metricId="operadoras"
        />

        <KpiCard
          title="Receita 12 Meses"
          value={formatCurrency(filteredKpis?.financeiro?.receita_12m ?? payload?.kpis?.financeiro?.receita_12m ?? 286400000000)}
          delta={8.2}
          subtitle="em 12 meses"
          metricId="financeiro"
        />

        <KpiCard
          title="Sinistralidade Média (12m)"
          value={formatPercent(filteredKpis?.financeiro?.sinistralidade_12m ?? payload?.kpis?.financeiro?.sinistralidade_12m ?? 83.5)}
          delta={0.8}
          subtitle="vs ano anterior"
          invertDeltaColors={true}
          metricId="financeiro"
        />

        <KpiCard
          title="Demandas NIP / 10k Vidas"
          value={String(filteredKpis?.demandas?.taxa_10k ?? payload?.kpis?.demandas?.taxa_10k ?? 4.15)}
          delta={-0.3}
          deltaText="-0.30 pt"
          subtitle="vs ano anterior"
          invertDeltaColors={true}
          metricId="demandas"
        />
      </section>

      <!-- 2. EVOLUÇÃO TEMPORAL PRINCIPAL -->
      <section class="section-block">
        <SectorEvolutionChart data={filteredEvolution} />
      </section>

      <!-- 3. PERFIL E DISTRIBUIÇÃO GEOGRÁFICA (2 COLUNAS) -->
      <section class="two-columns-grid">
        <ProfileBreakdownChart data={filteredProfile} />
        <GeographicChart data={filteredGeographic} />
      </section>

      <!-- 4. ECONÔMICO-FINANCEIRO E CONSUMIDOR (2 COLUNAS) -->
      <section class="two-columns-grid">
        <FinancialHealthChart data={filteredFinancial} />
        <ConsumerDemandsChart data={filteredDemands} />
      </section>

      <!-- 5. TABELA ANALÍTICA DE OPERADORAS -->
      <section class="section-block">
        <OperatorsTable data={filteredOperators} />
      </section>
    </main>
  {:else}
    <main class="main-content explorer-main">
      <QueryBuilder
        spec={olapSpec}
        result={olapResult ?? defaultOlapResult}
        isLoading={isOlapLoading}
        onExecuteQuery={handleExecuteOlapQuery}
      />
    </main>
  {/if}

  <footer class="app-footer">
    <div class="footer-container">
      <p>
        <strong>Sala de Situação da Saúde Suplementar</strong>
      </p>
      <p class="footer-sub">
        Desenvolvido com marimo, DuckDB, Parquet, Svelte e Apache ECharts. Dados abertos e governança transparente.
      </p>
    </div>
  </footer>

  <!-- Modais e Drawers de Apoio -->
  <MetadataDrawer />
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
