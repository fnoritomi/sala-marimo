# Arquitetura Técnica, Benchmarks e Análise Comparativa

Este documento descreve detalhadamente a engenharia de software, a modelagem de dados analíticos, os resultados empíricos de desempenho (latência, concorrência, memória) e o confronto arquitetural entre o paradigma **marimo + marimo-studio (Svelte + ECharts)** versus o modelo tradicional em **Dash (callbacks no servidor)**.

---

## 1. Arquitetura Técnica do Sistema

A nova geração da **Sala de Situação da ANS** foi projetada em uma arquitetura desacoplada de 4 camadas:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Navegador)                            │
│  Svelte 5 + TypeScript + Apache ECharts + Reactive Store               │
│  - Cross-filter instantâneo (sem requisição ao servidor)               │
│  - Renderização ECharts Canvas/SVG a 60 FPS                            │
│  - Brasil GeoJSON vetorial com taxa de cobertura e ranking             │
│  - Modais contextuais (Download DuckDB e Metadados Metodológicos)      │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ WebSocket / marimo Reactive RPC
                                    │ (Payload JSON estruturado)
┌───────────────────────────────────▼────────────────────────────────────┐
│                  RUNTIME REATIVO PYTHON (marimo)                       │
│  sala_situacao.py                                                      │
│  - Notebook reativo baseado em DAG (Grafo Acíclico Dirigido)          │
│  - Célula de projeção `dashboard_payload` vinculada à view studio      │
│  - Handlers de filtros de competência e exportação de dados            │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ Python In-Memory API
                                    │ (Thread-isolated Cursors)
┌───────────────────────────────────▼────────────────────────────────────┐
│                  CAMADA SEMÂNTICA (DuckDB Engine)                     │
│  src/analytics/service.py                                              │
│  - Respeito a medidas semi-aditivas (snapshot temporal em beneficiários)│
│  - Agregações aditivas para financeiro e demandas (fluxos)             │
│  - Predicate pushdown diretamente sobre Parquet                        │
│  - Thread safety com isolamento via `con.cursor()`                     │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ Direct I/O (Parquet Engine)
                                    │ ZSTD Compression / Columnar Read
┌───────────────────────────────────▼────────────────────────────────────┐
│                    STORAGE ANALÍTICO (Parquet)                         │
│  data/parquet/                                                         │
│  ├── beneficiarios/ano=YYYY/mes=MM/*.parquet  (Particionado)          │
│  ├── financeiro/ano=YYYY/mes=MM/*.parquet     (Particionado)          │
│  ├── demandas/ano=YYYY/mes=MM/*.parquet       (Particionado)          │
│  ├── operadoras/operadoras.parquet            (Dimensão)              │
│  └── populacao_uf/populacao_uf.parquet        (Dimensão Demográfica)  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Camada de Dados e Semântica (DuckDB + Parquet)

### 2.1. Particionamento e Compressão
- **Esquema:** Particionado por `ano=YYYY/mes=MM` para as tabelas fato (`beneficiarios`, `financeiro`, `demandas`), permitindo poda imediata de partições em consultas por período.
- **Compressão:** ZSTD com dicionário columnar. Redução média de ~78% em relação ao CSV correspondente.
- **Dimensões:** `operadoras` (com CNPJ, Razão Social, Porte, Modalidade, UF) e `populacao_uf` (projeções IBGE para cálculo da Taxa de Cobertura da Saúde Suplementar).

### 2.2. Rigor Semântico: Medidas Semi-aditivas vs. Aditivas
- **Beneficiários (Estoque / Snapshot Temporal):** O total de vidas no período $[t_1, t_2]$ não pode ser somado temporalmente ($\sum_{t} \text{vidas}_t$ é um erro grave que inflacionaria a população assistida). A agregação seleciona a última competência disponível no horizonte filtrado ($\text{beneficiários} = \sum_{\text{UF, Ops}} \text{vidas}_{\text{competência\_mais\_recente}}$).
- **Receitas, Despesas e Demandas (Fluxo Aditivo):** Medidas financeiras e demandas NIP são grandezas de fluxo, válidas sob soma em todo o intervalo temporal especificado.
- **Sinistralidade Operacional:** Calculada rigorosamente como:
  $$\text{Sinistralidade} = \frac{\sum \text{Despesas Assistenciais}}{\sum \text{Receitas de Contraprestações}} \times 100$$
- **Taxa de Notificação de Intermediação Preliminar (NIP por 10.000 vidas):**
  $$\text{Taxa NIP/10k} = \frac{\sum \text{Demandas}}{\text{Beneficiários Atuais}} \times 10.000$$

---

## 3. Benchmarks de Desempenho

### 3.1. Benchmark de Latência DuckDB Puro (`benchmark_duckdb.py`)
Medições executadas em processador x86_64, consultando fatos particionados diretamente via DuckDB em memória:

| Módulo de Consulta | Dataset Dev (~500k linhas) | Dataset Realista (~3.77M linhas) | Meta do Projeto | Status |
|---|---|---|---|---|
| **KPIs Executivos (Snapshot + Finanças + NIP)** | 3.52 ms | 9.42 ms | < 500 ms | **Aprovado (53x mais rápido)** |
| **Série Temporal Evolutiva (36 meses)** | 3.01 ms | 6.84 ms | < 500 ms | **Aprovado (73x mais rápido)** |
| **Perfil por Contratação & Modalidade** | 2.15 ms | 4.98 ms | < 500 ms | **Aprovado (100x mais rápido)** |
| **Distribuição Geográfica + Cobertura UF** | 3.24 ms | 7.15 ms | < 500 ms | **Aprovado (70x mais rápido)** |
| **Evolução Financeira & Sinistralidade** | 2.87 ms | 5.31 ms | < 500 ms | **Aprovado (94x mais rápido)** |
| **Demandas do Consumidor (Tempo + Temas)** | 3.10 ms | 6.72 ms | < 500 ms | **Aprovado (74x mais rápido)** |
| **Ranking Top 15 Operadoras** | 4.29 ms | 11.87 ms | < 500 ms | **Aprovado (42x mais rápido)** |
| **Média Ponderada da Jornada Completa** | **22.18 ms** | **52.29 ms** | **< 500 ms** | **Aprovado (9.5x superior à meta)** |

---

### 3.2. Benchmark de Concorrência e Escalabilidade (`benchmark_concurrency.py`)

Simulação de usuários concorrentes executando jornadas analíticas simultâneas (cada requisição executa 5 consultas completas de filtros combinados: UF + Modalidade + Assistência):

#### Dataset Dev (Particionado ZSTD):
| Concorrência | Latência Média | P50 (ms) | P95 (ms) | QPS (Jornadas/s) | Memória Total RSS | Memória / Sessão | Taxa de Erro |
|---|---|---|---|---|---|---|---|
| **1 sessão** | 73.75 ms | 71.20 ms | 87.34 ms | 13.5 req/s | 113.0 MB | 41.3 MB (base) | **0.00%** |
| **10 sessões** | 361.48 ms | 361.93 ms | 438.21 ms | 26.1 req/s | 151.4 MB | 7.97 MB | **0.00%** |
| **25 sessões** | 757.75 ms | 860.95 ms | 937.95 ms | 27.8 req/s | 187.6 MB | 4.63 MB | **0.00%** |
| **50 sessões** | 925.60 ms | 935.57 ms | 1045.95 ms | 26.7 req/s | 201.9 MB | 2.60 MB | **0.00%** |
| **100 sessões**| 981.59 ms | 988.04 ms | 1041.68 ms | 26.5 req/s | 210.6 MB | **1.39 MB** | **0.00%** |

#### Dataset Realista (3.77 Milhões de Linhas):
| Concorrência | Latência Média | P50 (ms) | P95 (ms) | QPS (Jornadas/s) | Memória Total RSS | Memória / Sessão | Taxa de Erro |
|---|---|---|---|---|---|---|---|
| **1 sessão** | 156.46 ms | 158.12 ms | 185.42 ms | 6.4 req/s | 120.6 MB | 49.0 MB (base) | **0.00%** |
| **10 sessões** | 920.27 ms | 904.39 ms | 1111.77 ms | 10.1 req/s | 158.2 MB | 8.66 MB | **0.00%** |
| **25 sessões** | 1800.38 ms | 1862.64 ms | 1980.86 ms | 9.8 req/s | 190.2 MB | 4.74 MB | **0.00%** |
| **50 sessões** | 1778.99 ms | 1909.86 ms | 1968.22 ms | 10.0 req/s | 198.4 MB | 2.54 MB | **0.00%** |
| **100 sessões**| 1826.11 ms | 1851.95 ms | 1995.80 ms | 9.7 req/s | 189.6 MB | **1.18 MB** | **0.00%** |

**Principais Conclusões de Desempenho:**
1. **Zero erros de concorrência:** O uso de cursores isolados por thread (`engine.get_cursor()`) garantiu 100% de estabilidade e ausência de contenção de travas de memória no DuckDB.
2. **Consumo de memória estável:** Mesmo com 100 sessões ativas consultando milhões de registros, o overhead por sessão é de apenas **1.18 MB a 1.39 MB**, mantendo a memória total do processo abaixo de **210 MB**.
3. **Escala de Throughput:** O motor analítico sustentou de 10 a 28 jornadas analíticas complexas por segundo de forma ininterrupta.

---

## 4. Análise Comparativa: marimo-studio + Svelte vs. Dash Tradicional

A tabela a seguir contrasta a arquitetura implementada com a solução convencional baseada em **Dash (Plotly + Flask + Server Callbacks)**:

| Dimensão Técnica / UX | Abordagem Tradicional Dash (Server-Centric) | Nova Geração: marimo-studio + Svelte + ECharts |
|---|---|---|
| **Paradigma de Execução** | Servidor-centrado: Toda interação do usuário dispara um POST/WebSocket com callback em Python. | Híbrido Reativo: Computações analíticas agregadas via DuckDB/Python; renderização e cross-filter locais em Svelte. |
| **Cross-filter Interativo** | **Lento (200ms - 1500ms):** Clicar em uma UF no mapa faz round-trip ao servidor Flask, reexecuta filtros em Pandas e serializa novos gráficos Plotly. | **Instantâneo (0ms - 16ms / 60 FPS):** Clicar em uma UF no mapa atualiza a store reativa do Svelte no navegador; gráficos ECharts redesenham via canvas local. |
| **Volume de Dados na Rede** | **Pesado (Megabytes):** Cada callback transmite árvores JSON complexas (`figure.data` + `figure.layout`), sobrecarregando o cliente móvel. | **Levíssimo (Kilobytes):** Apenas vetores compactos de dados agregados são transmitidos. A lógica visual reside no bundle Svelte compilado. |
| **Renderização Gráfica** | DOM pesado / SVG excessivo (Plotly.js pode engasgar com milhares de pontos ou mapas detalhados). | Apache ECharts em Canvas otimizado com aceleração por hardware e suporte nativo a mapas GeoJSON complexos. |
| **Consumo de Memória do Servidor** | **Alto (50MB - 150MB por sessão):** Estados de sessão mantidos no backend, duplicando dataframes por worker gunicorn. | **Mínimo (~1.2 MB por sessão):** DuckDB executa sobre arquivos Parquet compartilhados com isolamento por cursor sem cópias. |
| **Capacidade de Concorrência** | Requer múltiplos workers WSGI pesados; escala limitada pelo GIL do Python e serialização JSON. | Excelente escala concorrente via motor C++ multi-thread do DuckDB e eventos leves no WebSocket do marimo. |
| **Acessibilidade e Semântica** | Dificuldade para customizar tags HTML semânticas (`<nav>`, `<header>`, `<main>`, `role="dialog"`, `aria-*`). | Controle total do DOM via Svelte, com foco em conformidade WCAG 2.1 AA, labels de acessibilidade e navegação por teclado. |
| **Extensibilidade Visual** | Amarrado aos componentes do ecossistema Dash/Dash Bootstrap. | Ecossistema completo da Web moderna: Svelte 5, Tailwind/CSS modular, Lucide Icons, Apache ECharts, Canvas API. |

---

## 5. Conclusão da Validação Técnica

A arquitetura adotada demonstra que:
1. O **DuckDB** atuando diretamente sobre arquivos **Parquet particionados** elimina a necessidade de bancos relacionais legados ou cubos OLAP pesados (como Pentaho Mondrian), atingindo latências na ordem de **milissegundos**.
2. A integração **marimo-studio** com **Svelte + Apache ECharts** proporciona uma experiência de usuário de nível produto moderno (60 FPS, cross-filtering sem latência de rede, acessível e responsiva), preservando a fidelidade metodológica das métricas regulatórias da ANS.
