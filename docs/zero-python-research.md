# Pesquisa Técnica: Publicação Estática Zero-Python com marimo-studio

**Data:** Outubro de 2026  
**Ambiente:** marimo 0.25.0, marimo-studio 0.2.3, Python 3.12, DuckDB 1.4.x, Svelte 5, Vite 8, Apache ECharts 5.6.0  
**Contexto:** Sala de Situação da ANS — Avaliação de Distribuição Estática via CDN / GitHub Pages

---

## 1. Visão Geral da Arquitetura Zero-Python

O runtime `zero-python` do `marimo-studio` foi concebido para transformar notebooks interativos com views customizadas em sites estáticos puros, eliminando completamente a dependência de um servidor de aplicação Python ou de interpretadores pesados WebAssembly (Pyodide) no navegador do visitante.

```text
+-------------------------------------------------------------------------+
|                              FASE DE BUILD                              |
|                                                                         |
|  Parquet Files (1 MB a 250 MB)                                          |
|         │                                                               |
|         ▼                                                               |
|  DuckDB Engine (Python In-Memory)                                       |
|         │                                                               |
|         ▼                                                               |
|  Notebook marimo (sala_situacao.py)                                     |
|         │                                                               |
|         ▼                                                               |
|  Cálculo das Projeções (dashboard_payload / Cubo Analítico)             |
|         │                                                               |
|         ▼                                                               |
|  marimo-studio view export --runtime zero-python                        |
|    ├── Vite/Deno: Bundling de Svelte 5 + ECharts (JS/CSS)               |
|    └── Serialização: Geração de index.json das variáveis projetadas     |
|         │                                                               |
|         ▼                                                               |
|  Diretório dist/ (HTML estático + JS/CSS + JSON pré-calculado)          |
+-------------------------------------------------------------------------+
                                    │
                                    ▼ (Deploy estático)
+-------------------------------------------------------------------------+
|                               DISTRIBUIÇÃO                              |
|  GitHub Pages / CDN (Cloudflare, CloudFront, Fastly)                    |
+-------------------------------------------------------------------------+
                                    │
                                    ▼ (HTTP GET)
+-------------------------------------------------------------------------+
|                           NAVEGADOR DO USUÁRIO                          |
|                                                                         |
|  [x] Sem Python                                                         |
|  [x] Sem DuckDB Python                                                  |
|  [x] Sem Servidor marimo / Sem WebSockets                               |
|  [x] Sem API própria de backend                                         |
|                                                                         |
|  Execução:                                                              |
|    1. Carrega index.html com <base href="./">                           |
|    2. Baixa bundle Svelte 5 + Apache ECharts (~700 KB gzip)             |
|    3. Baixa projeção index.json (~80 KB gzip)                           |
|    4. Svelte reativo executa filtros e cross-filter em 0 a 16 ms        |
|    5. ECharts renderiza em Canvas a 60 FPS                              |
|    6. Download CSV via Blob client-side                                 |
+-------------------------------------------------------------------------+
```

---

## 2. Respostas aos 10 Tópicos Obrigatórios

### 2.1. O que é executado no build?
Durante a fase de build (`marimo-studio view export ... --runtime zero-python`):
1. **Python & DuckDB:** O motor analítico Python carrega os Parquet particionados do diretório `data/`, executa consultas SQL analíticas agregadas (Cubo multidimensional de beneficiários, evolução histórica de 36 meses, perfil contratual e por modalidade, fatos econômico-financeiros do DIOPS, demandas NIP por tema, e ranking das principais operadoras).
2. **Avaliação Reativa do Grafo marimo:** O marimo avalia todas as células do notebook até atingir a estabilidade do grafo DAG de dependências, computando a variável central exportada (`dashboard_payload`).
3. **Bundler Web (Vite + Deno):** O marimo-studio executa o compilador Svelte 5, transformando componentes `.svelte` e código TypeScript em artefatos estáticos minificados (`dist/assets/index-[hash].js` e `dist/assets/index-[hash].css`).
4. **Preflight estático:** Valida a integridade dos pontos de montagem, elementos `mo-value`, referências cruzadas e ausência de falhas estruturais (0 diagnósticos reportados).
5. **Geração dos artefatos estáticos:** Gera `index.html` com suporte a URLs relativas (`<base href="./">`), o script de bootstrap `zero-python.js`, e salva o payload serializado em `_marimo-studio/views/<view>/zero-python/<hash>/index.json`.

### 2.2. O que permanece no navegador do visitante?
Absolutamente nenhum ambiente de execução Python:
- **Zero CPython / Zero Backend:** Não há servidor intermediário, containers Docker ou processos Python ouvindo requisições HTTP ou WebSockets.
- **Zero Pyodide / WebAssembly Python:** A página não faz download de runtimes WASM pesados (como pyodide.asm.js de 30+ MB).
- **Apenas Runtime Web Padrão:** JavaScript ES moderno (V8/SpiderMonkey/JavaScriptCore), Svelte 5 em modo cliente, Apache ECharts desenhando em `<canvas>`, CSS responsivo, manipulação de History/URL API e geração de downloads via `Blob` nativo.

### 2.3. Como os estados reativos são preparados?
O `marimo-studio` no modo `zero-python` adota o conceito de **Prepared Runtime**:
- Ele executa as células do notebook no ambiente de build local e captura o valor serializável de cada variável vinculada a atributos `mo-value` no template HTML/Svelte.
- Esses valores são gravados em disco como payloads JSON indexados por um hash determinístico da configuração.
- No carregamento da página, o helper `observeMarimoValue` (injetado via `src/lib/marimo-value.ts` ou pelo bootstrap `zero-python.js`) lê esses dados instantaneamente e alimenta as stores e sinais reativos do Svelte.

### 2.4. Como os filtros são representados?
Existem dois modelos possíveis de representação de filtros em arquiteturas estáticas:
- **Modelo A (Multi-State Combinatório):** Cada tupla de controles `(UF, Assistência, Contratação, Modalidade)` gera um estado estático pré-computado independente em arquivos JSON distintos.
- **Modelo B (Cubo Multidimensional Agregado + Filtragem Client-Side):** Um único estado analítico pré-calculado entrega uma estrutura relacional compacta contendo granularidade agregada mínima necessária. O frontend Svelte aplica as seleções e filtros instantaneamente em memória (0 a 16 ms) via derivados reativos (`$derived.by`).

O modelo adotado com sucesso nesta implementação é a **Estratégia B**, pois garante latência imperceptível e imunidade à explosão combinatória.

### 2.5. Como o frontend acessa resultados preparados?
O host de projeção no componente principal `App.svelte`:
```html
<span
  id="dashboard-data"
  hidden
  mo-value="dashboard_payload"
  use:observeMarimoValue={{
    onValue: (value: any) => { payload = value; },
    onError: (err) => { console.warn("Marimo projection:", err); }
  }}
></span>
```
O script `zero-python.js` lê o `_marimo-studio/views/dashboard/zero-python/.../index.json` gravado pelo build e dispara o callback `onValue` com o objeto completo decodificado.

### 2.6. Limitações de número de estados
Na Estratégia A:
- O produto cartesiano completo de 27 UFs $\times$ 3 tipos de assistência $\times$ 4 modalidades de contratação $\times$ 8 modalidades de operadora $\times$ 36 competências temporais resulta em **233.280 estados teóricos**.
- Mesmo filtrando apenas combinações com dados reais (> 25.000 estados válidos), exportar cada estado como um JSON independente levaria a builds com horas de duração, dezenas de gigabytes em disco e impossibilidade de deploy no GitHub Pages.
Na Estratégia B:
- O número de estados preparados necessários é **exatamente 1** ($O(1)$). O cubo agregado pesa ~830 KB (~80 KB gzip), viabilizando build em menos de 30 segundos.

### 2.7. Limitações documentadas de tamanho
- **GitHub Pages:**
  - Limite recomendado do repositório: 1 GB.
  - Limite rígido de arquivo individual: 100 MB.
  - Limite de largura de banda mensal: 100 GB.
- **Navegadores Mobile / Low-End:**
  - O payload transferido inicial (HTML + JS + CSS + JSON) deve se manter idealmente abaixo de 2 MB (compactado) para atender aos padrões Core Web Vitals (LCP < 2,5 s em conexões 4G).
  - O heap de memória JavaScript deve permanecer inferior a 100 MB para evitar descarte de abas pelo sistema operacional móvel.

### 2.8. Recursos incompatíveis
Recursos que não podem ser atendidos em zero-python puro sem uma camada de backend/API:
1. Consultas SQL arbitrárias ou ad-hoc formuladas pelo usuário em tempo de execução.
2. Atualização em tempo real (push via WebSockets) de novos dados sem um novo build/deploy.
3. Autenticação restrita por usuário com Row-Level Security (RLS) dinâmico.
4. Exportação sob demanda de microdados não agregados (ex.: 50 milhões de linhas detalhadas de beneficiários individuais).

### 2.9. Comportamento de downloads
- **Contextual por Visualização:** Perfeitamente viável em zero-python. Os dados exibidos em cada gráfico ou tabela já residem na memória do navegador. A geração do CSV é feita instantaneamente em TypeScript com inclusão de BOM UTF-8 (`\uFEFF`) e disparada via `URL.createObjectURL(new Blob(...))`.
- **Download Massivo da Base Completa (Dados Abertos):** Deve ser desacoplado do dashboard, disponibilizando links diretos para repositórios estáticos (S3, Cloudflare R2 ou Portal de Dados Abertos da ANS) com arquivos Parquet mensais comprimidos em ZSTD.

### 2.10. Comportamento de custom views
- As views customizadas do `marimo-studio` (como a implementada em Svelte 5 + TypeScript + Vite) são tratadas como cidadãos de primeira classe no build. O processo empacota a aplicação SPA completa, gerando um site autocontido que funciona de forma desacoplada do ecossistema marimo tradicional.
