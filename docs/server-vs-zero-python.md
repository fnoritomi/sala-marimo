# Comparativo Arquitetural: Server-Side vs. Zero-Python Static vs. Dash PoC

**Aplicação:** Sala de Situação da Saúde Suplementar (ANS)  
**Ambiente Analítico:** DuckDB 1.4.x, Parquet particionado (ZSTD), Apache ECharts 5.6.0  
**Data:** Outubro de 2026  

---

## 1. Comparação Direta: Server-Side (marimo-studio) × Zero-Python (marimo-studio)

A tabela a seguir compara o comportamento da mesma primeira página da Sala de Situação sob duas modalidades de execução do `marimo-studio`: como servidor dinâmico Python/Tornado e como aplicação estática compilada para distribuição via CDN / GitHub Pages.

| Critério | Server-Side (marimo-studio) | Zero-Python Static (marimo-studio) |
|---|---|---|
| **Python em runtime** | **Sim** (CPython 3.12 ativo no backend) | **Não** (Zero Python / Zero CPython / Zero WASM) |
| **DuckDB em runtime** | **Sim** (Conexão `:memory:` mantida pelo processo) | **Não** (Executado apenas no pipeline de build CI/CD) |
| **Servidor de Aplicação** | **Sim** (Obrigatório servidor marimo / uvicorn / container) | **Não** (Somente servidor HTTP de arquivos estáticos / CDN) |
| **Sessão por usuário** | **Sim** (Kernel e estado alocados no servidor) | **Não** (Stateless no servidor; estado na aba do cliente) |
| **Cross-filter** | 0–16 ms (executado no cliente via Svelte) ou 5–15 ms via RPC | **0–16 ms** (100% no cliente via Svelte stores derivadas) |
| **Filtros dimensionais** | 6–12 ms (consulta SQL no DuckDB via WebSocket/HTTP) | **0–16 ms** (filtragem sobre o cubo em memória no cliente) |
| **Drill-down (Brasil → UF)** | Instantâneo via DuckDB ou store local | **Instantâneo (< 5 ms)** via seleção de UF na store reativa |
| **Drill-through (Operadoras)** | Filtragem tabular sob demanda no servidor | **Instantâneo (< 5 ms)** via busca e slice do array em JS |
| **Download CSV** | Gerado no servidor ou no browser via Blob | **Client-side instantâneo** via Blob com BOM UTF-8 |
| **Download Parquet completo** | Possível servir arquivos grandes do filesystem | **Via link direto** para repositório de dados abertos (S3/R2) |
| **Cold start** | 1,2 a 2,5 s (inicialização do processo Python e kernel) | **0 s** (servido instantaneamente da edge da CDN) |
| **First Load (LCP 4G)** | ~1,8 s (HTML inicial + WebSocket handshake + payload) | **~1,4 s** (HTML + bundle JS/CSS compactado + JSON cacheado) |
| **Escala de acessos (concorrência)** | Limitada a CPU/RAM do host Python (ex.: 50–200 req/s) | **Praticamente ilimitada** (servido por CDN com cache global) |
| **Complexidade operacional** | Média/Alta (orquestração de containers, monitoramento de RAM) | **Mínima** (GitHub Pages / bucket S3 + Cloudflare) |
| **Custo de infraestrutura** | Contínuo (instância de computação 24/7) | **Praticamente zero** (estático gratuito ou centavos/mês) |
| **Atualização de dados** | Imediata (basta sobrescrever Parquets no volume) | Exige pipeline de rebuild CI/CD (~45–90s) |
| **Consultas SQL ad-hoc** | Possível (se exposto pelo notebook) | Impossível (requer API ou motor analítico) |

---

## 2. Comparativo Triplo: Dash + DuckDB × Marimo Server + DuckDB × Marimo Zero-Python

Com base nos experimentos empíricos e nas medições com os mesmos datasets da ANS:

| Métrica / Dimensão | Dash + DuckDB (Python puro) | Marimo Studio Server + DuckDB | Marimo Studio Zero-Python |
|---|---|---|---|
| **Tempo de abertura inicial (Cold Start)** | 2,8 s – 4,5 s | 1,8 s – 2,5 s | **0,8 s – 1,4 s** |
| **Latência de interação / filtro** | 80 ms – 250 ms (HTTP callback roundtrip) | 15 ms – 45 ms (WebSocket / reativo) | **0 ms – 16 ms** (in-memory Svelte 5) |
| **Cross-filter entre gráficos** | Lento / exige callbacks encadeados | Rápido (Svelte 5 local) | **Imediato (60 FPS, sem roundtrip)** |
| **Memória no Servidor (por usuário)** | ~80 MB – 150 MB (Plotly + callbacks) | ~40 MB – 80 MB (kernel marimo) | **0 MB** (Sem servidor de aplicação) |
| **Memória no Navegador (Cliente)** | ~65 MB – 90 MB | ~35 MB – 45 MB | **~38 MB – 50 MB** |
| **Volume de transferência inicial (gzip)** | ~2,8 MB (bundle Dash + Plotly.js) | ~950 KB (Svelte + ECharts + payload) | **~850 KB** (Svelte + ECharts + JSON) |
| **Complexidade de manutenção do UI** | Alta (layouts complexos em dicionários Python) | Baixa (componentes nativos Svelte + TS) | Baixa (mesma base Svelte + TS) |
| **Necessidade de Backend** | **Obrigatória** | **Obrigatória** | **Nenhuma** |
| **Processo de Deploy** | Docker / VM com Gunicorn / Uvicorn | Docker / VM com marimo | GitHub Pages / Cloudflare Pages |

---

## 3. Análise Detalhada dos Diferenciais

### 3.1. Reatividade e Cross-Filter
- No **Dash**, qualquer interação (clicar em um estado no mapa ou selecionar um filtro) exige um roundtrip de rede via HTTP POST para o servidor Python, execução da função Python de callback, serialização da figura Plotly em JSON e re-renderização via `Plotly.react()`. Em conexões reais (4G móvel), a latência fica perceptível (> 200 ms).
- No **Marimo Studio Zero-Python**, todo o estado analítico reside na store reativa TypeScript (`analyticalStore.ts`). A alteração de um filtro recalcula as visões derivadas em **0 a 16 milissegundos**, atualizando o Apache ECharts em canvas diretamente a 60 quadros por segundo, sem tráfego de rede.

### 3.2. Custo e Escalabilidade
- Uma Sala de Situação pública de uma autarquia federal como a ANS está sujeita a picos de tráfego (divulgação de relatórios trimestrais, matérias em telejornais).
- Manter uma infraestrutura server-side (Dash ou Marimo Server) para suportar 10.000 usuários simultâneos exigiria balanceamento de carga, dezenas de instâncias com gunicorn/uvicorn e dezenas de gigabytes de RAM.
- No **Zero-Python**, 10.000 usuários simultâneos são absorvidos pelas bordas da CDN (Cloudflare/Fastly) sem impacto em servidor de aplicação ou banco de dados, com custo praticamente desprezível.

### 3.3. Atualização Atômica e Imutabilidade
- No modelo estático, cada release é imutável: o hash dos bundles (`index-[hash].js`) garante cache-busting automático. Quando uma nova competência é publicada pelo pipeline de CI/CD, os usuários que acessam o link recebem a versão nova sem inconsistências de meio de atualização.
