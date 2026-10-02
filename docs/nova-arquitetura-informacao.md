# Nova Arquitetura de Informação: Sala de Situação Moderna da ANS

Este documento descreve a reorganização analítica e funcional da Sala de Situação da ANS, substituindo a navegação legada orientada a sistemas internos por uma arquitetura orientada às **perguntas analíticas centrais** do setor.

---

## 1. Princípios de Design e Arquitetura

1. **Perguntas Estratégicas como Guias de Layout**: Cada seção da interface responde diretamente a uma pergunta de negócio clara.
2. **Progressive Disclosure**:
   - Nível 1: Visão Executiva (KPIs, tendências e deltas acima da dobra).
   - Nível 2: Exploração Interativa (cross-filtering, zoom temporal, alternância de visualizações).
   - Nível 3: Detalhamento sob Demanda (Drawer de Metadados, Tabela explorável com busca, Download de dados).
3. **Coerência Reativa Semântica**:
   - Estados de filtro globais e locais centralizados em um store TypeScript.
   - Feedback visual imediato (< 100 ms) para ações do usuário (clique em UF, mudança de agrupamento).
4. **Respeito a Medidas de Estoque (Semi-Aditivas)**:
   - Apresentação transparente das datas de competência para beneficiários (snapshot), evitando soma espúria entre meses.
5. **Acessibilidade e Responsividade**:
   - Suporte nativo a telas desktop (visão ampla em grid), tablets (reordenação modular) e dispositivos móveis (coluna única com gráficos adaptados).

---

## 2. As 7 Perguntas Centrais e Estrutura da Página Principal

```text
┌────────────────────────────────────────────────────────────────────────┐
│ [GOV.BR / ANS]  Sala de Situação da Saúde Suplementar                  │
│ Monitoramento Estratégico do Setor               Competência: Jun/2026 │
├────────────────────────────────────────────────────────────────────────┤
│ BARRA DE FILTROS GLOBAIS                                               │
│ [ Assistência: Todas ▾ ] [ Contratação: Todas ▾ ] [ Modalidade: Todas ▾ ]
│ Chips Ativos: [ UF: Brasil ] [ Limpar Todos ⟲ ]           [ Download ⤓ ]
├────────────────────────────────────────────────────────────────────────┤
│ 1. QUAL O TAMANHO ATUAL DO SETOR E O QUE MUDOU RECENTEMENTE?           │
│                                                                        │
│ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌───────────┐│
│ │ BENEFICIÁRIOS  │ │ OPERADORAS     │ │ RECEITA (12M)  │ │ DEMANDAS  ││
│ │ 52,4 mi vidas  │ │ 678 ativas     │ │ R$ 286,4 bi    │ │ 4,2 /10k  ││
│ │ ▲ +1,8% em 12m │ │ ▼ -12 em 12m   │ │ ▲ +8,2% em 12m │ │ ▼ -0,4 pt ││
│ │  ▂▃▄▅▆▇        │ │ ▇▆▅▄▃          │ │   ▂▃▄▅▆▇       │ │ ▄▅▄▃▂     ││
│ └────────────────┘ └────────────────┘ └────────────────┘ └───────────┘│
├────────────────────────────────────────────────────────────────────────┤
│ 2. COMO O SETOR ESTÁ EVOLUINDO NO TEMPO?                               │
│ [ 12 Meses ] [ 24 Meses ] [ 36 Meses ] [ Todo o Período ]  [ Métricas ]│
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ Série Temporal ECharts: Beneficiários Médicos vs Odontológicos     │ │
│ │ (Com linha de tendência e DataZoom deslizante)                     │ │
│ └────────────────────────────────────────────────────────────────────┘ │
├───────────────────────────────────┬────────────────────────────────────┤
│ 3. COMO OS BENEFICIÁRIOS ESTÃO    │ 4. ONDE ESTÃO OS BENEFICIÁRIOS?    │
│    DISTRIBUÍDOS? (PERFIL)         │    (DISTRIBUIÇÃO GEOGRÁFICA)       │
│                                   │                                    │
│ [ Contratação ]     [ Modalidade ]│ [ Mapa Coroplético ] [ Ranking UF ]│
│ ┌─────────────────┐ ┌───────────┐ │ ┌────────────────────────────────┐ │
│ │ Empresarial 70% │ │ Coop. 38% │ │ │ Mapa do Brasil ECharts         │ │
│ │ Individual  17% │ │ Med.Grp39%│ │ │ (Clique na UF para Cross-Filter)│ │
│ │ Adesão      13% │ │ Segur. 12%│ │ │ Escala de Cobertura Populacional│ │
│ │ (Barras 100%)   │ │ Autog. 9% │ │ │ SP: 36,4%  RJ: 11,2%  MG: 9,8% │ │
│ └─────────────────┘ └───────────┘ │ └────────────────────────────────┘ │
├───────────────────────────────────┴────────────────────────────────────┤
│ 5. QUAL É A SITUAÇÃO ECONÔMICO-FINANCEIRA DO SETOR?                    │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ Gráfico Comparativo: Receitas x Despesas Assistenciais (R$ bi)     │ │
│ │ com Linha de Sinistralidade do Setor (%) e Margem Operacional      │ │
│ └────────────────────────────────────────────────────────────────────┘ │
├───────────────────────────────────┬────────────────────────────────────┤
│ 6. QUAL É A EXPERIÊNCIA DO        │ 7. QUEM SÃO AS PRINCIPAIS          │
│    CONSUMIDOR COM OS PLANOS?      │    OPERADORAS DO MERCADO?          │
│                                   │                                    │
│ ┌───────────────────────────────┐ │ ┌────────────────────────────────┐ │
│ │ Taxa de Reclamações NIP /10k  │ │ │ Tabela Top 15 Operadoras       │ │
│ │ Motivos: Assistencial 72%     │ │ │ [Buscar por nome...]           │ │
│ │          Não Assistencial 28% │ │ │ Operadora │ Vidas │ Sinistr │IGR││
│ │ Resolutividade NIP: 88,4%     │ │ │ Drill-through detalhado        │ │
│ └───────────────────────────────┘ │ └────────────────────────────────┘ │
└───────────────────────────────────┴────────────────────────────────────┘
```

---

## 3. Fluxos de Interação e Jornada do Usuário

### 3.1 Fluxo 1: Investigação Regional com Cross-Filter Instantâneo
1. O usuário visualiza o panorama nacional consolidado.
2. Na seção geográfica, o usuário clica sobre o estado do **Rio de Janeiro (RJ)** no mapa ou no ranking.
3. **Efeito Imediato no Frontend**:
   - O chip de filtro `[ UF: Rio de Janeiro ✕ ]` surge na barra de filtros.
   - O gráfico de Evolução Histórica passa a exibir a série histórica do RJ.
   - O perfil de contratação e modalidades reajusta-se para a realidade do RJ.
   - A sinistralidade e as demandas NIP exibem os indicadores do RJ.
   - A tabela de operadoras filtra as operadoras atuantes no RJ.
4. O usuário clica no `✕` do chip e todo o painel retorna ao panorama nacional em menos de 100 ms.

### 3.2 Fluxo 2: Investigação por Segmento Assistencial
1. O tomador de decisão deseja avaliar especificamente os planos **Exclusivamente Odontológicos**.
2. Altera o filtro superior para `Assistência = Odontológica`.
3. Todos os totalizadores e séries são recalculados para o universo odontológico, exibindo métricas de ticket médio, sinistralidade específica e operadoras odontológicas líderes.

### 3.3 Fluxo 3: Transparência Metodológica (Progressive Disclosure)
1. Ao pairar sobre o indicador de Sinistralidade ou clicar no ícone `[ⓘ Metadados]`, abre-se o **Metadata Drawer**.
2. O usuário consulta:
   - Fórmula: `(Despesas com Eventos e Sinistros / Contraprestações Efetivas) * 100`
   - Fonte: DIOPS/ANS (Documento de Informações Periódicas das Operadoras)
   - Periodicidade: Trimestral
   - Unidade: Porcentagem (%)
   - Observações regulatórias e limites prudenciais da ANS.

### 3.4 Fluxo 4: Exportação de Dados Analíticos
1. O usuário aciona o botão `[ Download ]` no topo ou no rodapé de um gráfico específico.
2. O modal permite escolher:
   - **CSV**: formato tabular para Excel / Google Sheets com dados agregados dos filtros ativos.
   - **Parquet**: arquivo analítico compactado de alta performance com dados completos.
3. O download é processado diretamente pelo DuckDB, sem sobrecarregar a memória do navegador.
