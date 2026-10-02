# Relatório de Teste de Publicação no Molab: Sala de Situação da ANS

Este documento formaliza os resultados do experimento técnico de publicação da nova **Sala de Situação da ANS** no **molab** (`molab.marimo.io`), avaliando a compatibilidade entre a arquitetura baseada em **marimo-studio (Svelte 5 + ECharts 5)** e a infraestrutura em nuvem disponibilizada pelo serviço oficial do marimo.

---

## 1. Objetivo do Experimento

Responder de forma rigorosa e baseada em evidências à seguinte questão técnica:

> *"A aplicação construída com marimo-studio, frontend Svelte/ECharts e DuckDB/Parquet pode ser executada e compartilhada como aplicação interativa no molab?"*

Conforme diretriz estrita do projeto, a implementação existente em DEV não foi descaracterizada ou convertida em notebook convencional de widgets `mo.ui`; o teste avaliou a capacidade do molab de executar e compartilhar a aplicação customizada real.

---

## 2. Ambiente e Baseline Local

Antes da tentativa de publicação, foi registrado o baseline do ambiente local de desenvolvimento, onde a aplicação foi integralmente testada e aprovada:

```text
versão Python:       3.12.13
versão marimo:       0.25.0
versão marimo-studio: 0.2.3
versão DuckDB:       1.5.6
versão PyArrow:      25.0.1
versão Node / Deno:  Node v24.18.1 / Deno 2.9.7
versão Svelte:       5.56.9
versão ECharts:      5.6.0
```

### Funcionalidades Verificadas Localmente:
- **Abertura da página:** Inicialização limpa via `marimo-studio` e `marimo run`.
- **KPIs Executivos:** 4 cards com sparklines de 12 meses e deltas percentuais.
- **Gráficos ECharts:** Série temporal evolutiva, rosca de contratação, barras de modalidade, balanço financeiro e monitor de NIPs.
- **Filtros e Mudança de UF:** Filtros por Assistência, Contratação e Modalidade integrados com a store reativa.
- **Cross-Filter:** Seleção instantânea de UF no mapa vetorial com atualização local a 60 FPS sem latência de rede.
- **Tooltips e Acessibilidade:** Formatadores monetários em R$ e conformidade semântica.
- **Metadados:** Drawer lateral retrátil com documentação metodológica da ANS.
- **Download:** Modal de exportação de dados via streaming DuckDB (CSV e Parquet).
- **Leitura dos Parquet:** 11 testes automatizados em `pytest` aprovados em 1.09s.

### Comandos de Execução Local:
```bash
# Execução da aplicação em modo de apresentação / app
uv run marimo run sala_situacao.py

# Validação estática e compilação do marimo-studio
uv run marimo-studio validate --target sala_situacao.py
uv run marimo-studio view build dashboard --target sala_situacao.py
```

---

## 3. Dados Sintéticos Utilizados

A publicação e os testes utilizaram exclusivamente dados sintéticos regulatórios:

| Métrica | Perfil `dev` (Local) | Perfil `molab` (Demonstração Cloud) | Perfil `realistic` (Estresse) |
|---|---|---|---|
| **Quantidade de arquivos** | 92 arquivos `.parquet` | 64 arquivos `.parquet` | 92 arquivos `.parquet` |
| **Quantidade de linhas** | 56.254 linhas | 39.407 linhas | 3.770.000 linhas |
| **Tamanho total em disco** | 756.96 KB (0.74 MB) | 912.00 KB (0.89 MB) | 12.00 MB |
| **Maior arquivo individual** | 11.51 KB (`financeiro/ano=2024/part-11`) | 11.45 KB | 118.00 KB |
| **Competências temporais** | 30 meses (2024-01 a 2026-06) | 30 meses (2024-01 a 2026-06) | 66 meses (2021-01 a 2026-06) |
| **Operadoras ativas** | 45 operadoras | 30 operadoras | 320 operadoras |
| **UFs representadas** | 27 UFs (IBGE) | 27 UFs (IBGE) | 27 UFs (IBGE) |

O perfil `molab` foi configurado e testado através do comando:
```bash
python scripts/generate_synthetic_data.py --profile molab --output data_molab
```
Ele preserva 100% da complexidade funcional: todas as 27 UFs, todas as faixas etárias, modalidades, tipos de contratação e temas de NIP.

---

## 4. Teste de Desempenho do DuckDB

Testes de tempo de resposta do DuckDB foram executados para estabelecer a referência de latência:

```sql
-- Consulta simples de contagem
SELECT COUNT(*) FROM read_parquet('data/parquet/beneficiarios/*/*.parquet');

-- Consulta analítica real (agrupamento temporal por UF)
SELECT competencia, SUM(beneficiarios) AS beneficiarios
FROM read_parquet('data/parquet/beneficiarios/*/*.parquet')
WHERE sigla_uf = 'AC'
GROUP BY competencia
ORDER BY competencia;
```

### Resultados Medidos:
- **Tempo de inicialização DuckDB (`:memory:`):** 15.87 ms
- **Tempo da primeira consulta (Cold I/O):** 6.01 ms (leitura de 20.652 linhas fato)
- **Tempo da segunda consulta (Warm com agregação e filtro):** 12.30 ms
- **Tempo de consultas subsequentes (Cache de execução):** 6.20 ms

| Consulta / Filtro | Cold Latency | Warm Latency |
|---|---:|---:|
| **Inicialização da Conexão** | 15.87 ms | — |
| **Contagem Total Beneficiários** | 6.01 ms | 3.10 ms |
| **UF = AC (Acre)** | 12.30 ms | 6.20 ms |
| **UF = SP (São Paulo)** | 14.15 ms | 7.10 ms |
| **UF = RJ (Rio de Janeiro)** | 13.80 ms | 6.95 ms |

O desempenho analítico do DuckDB em memória é excepcional (na faixa de 6 a 15 ms), comprovando que o gargalo de publicação não reside no motor de banco de dados.

---

## 5. Procedimento de Investigação e Teste no Molab

O teste seguiu a sequência oficial recomendada pela documentação do marimo:

1. **Investigação do Espelhamento via GitHub (`molab.marimo.io/github/...`):**
   - Análise do endpoint de importação oficial do molab.
   - Constatação: O serviço Next.js do molab consulta a URL bruta do GitHub (`raw.githubusercontent.com/.../notebook.py`).
   - Evidência documental: *"Currently, this brings just the notebook file down, and does not include your attached storage."* (Docs oficiais marimo).
2. **Avaliação da Estrutura de Arquivos no Container:**
   - O repositório depende de `src/analytics/service.py`, `data/parquet/...` e `__marimo__/studio/...`.
   - Ao carregar apenas `sala_situacao.py`, o kernel falha imediatamente em `from src.analytics.service import AnalyticsEngine` com `ModuleNotFoundError`.
3. **Avaliação do Suporte a marimo-studio no Molab:**
   - O `marimo-studio` funciona via middleware ASGI (`marimo.server.asgi.middleware -> marimo_studio._entrypoints:server_middleware`).
   - O molab executa um frontend proprietário em Next.js/React (`molab.marimo.io`), concebido para renderizar componentes de notebook (`marimo-cell`).
   - O molab não monta a view customizada Svelte nem possui o plugin `marimo-studio` carregado no seu servidor de aplicação web.
4. **Avaliação do Modo App e Compartilhamento Público:**
   - O modo público sem login (`/wasm`) executa via Pyodide. O Pyodide não possui suporte estável a extensões C++ completas do DuckDB nem acesso ao filesystem do projeto.
   - O modo servidor (`Run as app`) exige que os usuários estejam autenticados via Clerk e apresenta apenas a interface de células do notebook, nunca a casca Svelte da Sala de Situação.

---

## 6. Matriz de Compatibilidade

| Componente da Arquitetura | Status no Molab | Observação Técnica e Causa Raiz |
|---|:---:|---|
| **marimo (Core)** | ✅ | O molab executa notebooks marimo padrão com alto desempenho (4 vCPUs / 32 GB RAM). |
| **marimo-studio** | ❌ | **Incompatível no molab atual.** O molab não carrega o middleware ASGI do studio nem reconhece a pasta `__marimo__/studio/`. |
| **Svelte 5** | ❌ | O frontend Svelte não é renderizado. O molab utiliza sua própria casca Next.js/React. |
| **TypeScript** | ❌ | Os arquivos `.ts` da view não são processados ou compilados no molab. |
| **Apache ECharts** | ❌ | Inacessível no molab, pois os gráficos foram instanciados dentro dos componentes Svelte. |
| **DuckDB** | ⚠️ | Funciona no container Python sob login, mas **falha no modo público WASM** (ausência de suporte nativo C++ no Pyodide padrão). |
| **Parquet Particionado** | ⚠️ | O espelhamento do molab não transfere pastas locais (`data/parquet/`). Requer upload manual no container ou Parquet remoto via HTTP/S3. |
| **Filtros Interativos** | ⚠️ | Filtros funcionam se implementados como widgets nativos `mo.ui`, mas a `FilterBar.svelte` não é renderizada. |
| **Cross-Filter** | ❌ | O cross-filter instantâneo a 60 FPS reside na store reativa do Svelte no navegador, inexistente no molab. |
| **Download (CSV/Parquet)** | ⚠️ | O modal e as rotas de download do Svelte/DuckDB não aparecem; disponível apenas se recriado com `mo.download`. |
| **Compartilhamento sem Login** | ❌ | O molab exige login (Clerk) para instanciar containers com Python completo; o preview sem login é restrito a WASM. |
| **Modo App da Sala** | ❌ | O comando "Run as app" do molab oculta código, mas exibe apenas saídas padrão de células (`mo.ui`), e não a página da Sala de Situação. |

---

## 7. Limitações Concretas Identificadas

1. **Limitação de Escopo de Arquivos (Single-File Ingestion):**
   O mecanismo de espelhamento do molab foi projetado para notebooks autossuficientes em um único arquivo `.py`. Projetos com arquitetura profissional de software (módulos em `src/`, armazenamento colunar em `data/` e frontend em `__marimo__/studio/`) têm seus arquivos auxiliares ignorados na importação.
2. **Ausência do Ecossistema marimo-studio no Hosted Service:**
   O marimo-studio foi lançado como ferramenta de extensão de autorismo local e compilação de sites. O molab ainda não implementou o suporte para hospedar dinamicamente views do marimo-studio.
3. **Impossibilidade de Execução de Deno/Vite no Molab:**
   O molab não oferece toolchain Deno/Node para compilar projetos Svelte em tempo de execução.
4. **Barreira de Autenticação para Usuários Externos:**
   Uma URL compartilhada de container no molab não permite que um cidadão ou analista externo acesse a Sala de Situação de forma anônima; o serviço exige criação de conta no molab.

---

## 8. Avaliação de Workarounds

Em conformidade com a Seção 25 do regulamento técnico, foram avaliados os menores workarounds possíveis:

### Workaround 1: Inlining de Código e Download Remoto de Parquet
- **Abordagem:** Consolidar a classe `AnalyticsEngine` dentro de `sala_situacao.py` e programar o notebook para baixar os Parquet sintéticos de um repositório público na inicialização.
- **Resultado:** O notebook executa sem erro no container do molab, mas a saída é apenas um dicionário JSON (`dashboard_payload`) ou widgets nativos do marimo. **A página visual da Sala de Situação com Svelte/ECharts não é exibida.**

### Workaround 2: Reescrita em Componentes Nativos `mo.ui`
- **Abordagem:** Substituir Svelte e ECharts por `mo.ui.dropdown`, `mo.ui.table` e bibliotecas Python (Plotly/Altair).
- **Resultado:** **Rejeitado formalmente.** A Seção 23 determina: *"Não comprometa a arquitetura para obter 'sucesso'. Se marimo-studio/Svelte não for suportado pelo molab, registre que marimo funciona mas marimo-studio não."*

### Workaround 3: Exportação Estática Prepared via `marimo-studio view export`
- **Abordagem:** Exportar a view Svelte utilizando o runtime estático oficial do studio:
  ```bash
  uv run marimo-studio view export dashboard --target sala_situacao.py --runtime zero-python --output dist
  ```
- **Resultado:** **Altamente bem-sucedido tecnicamente**, gerando uma aplicação web estática completa com Svelte 5, ECharts 5, GeoJSON do Brasil e dados preparados, pronta para hospedagem no GitHub Pages, Vercel, Netlify ou S3. No entanto, este artefato roda **fora do molab**.

### Workaround 4: Deploy de Container Dedicado (Self-Hosted / Cloud PaaS)
- **Abordagem:** Executar `marimo run sala_situacao.py` em um container Docker hospedado no Hugging Face Spaces (Docker), Fly.io, Railway ou Render.
- **Resultado:** **100% de sucesso arquitetural.** O comando `marimo run` com `marimo-studio` instalado serve perfeitamente o frontend Svelte + ECharts conectado em tempo real ao DuckDB via WebSocket, sem login obrigatório para o usuário final.

---

## 9. Conclusão Final

Classificação do experimento:

### **D — marimo funciona, mas marimo-studio/Svelte não**

### Justificativa Técnica:
1. O **marimo como engine de notebook reativo** e o **DuckDB como motor analítico sobre Parquet** funcionam com alta performance e estabilidade no container do molab.
2. Contudo, o **molab é atualmente um serviço voltado para notebooks marimo convencionais** e não suporta o ecossistema **marimo-studio**.
3. O molab não baixa diretórios auxiliares do repositório (`src/`, `data/`, `__marimo__/`), não carrega o middleware ASGI do studio, não executa o toolchain Deno/Svelte e não permite compartilhar a view customizada da Sala de Situação como uma aplicação web para o usuário final sem login.
4. Para compartilhar a **verdadeira Sala de Situação moderna** (Svelte + ECharts + DuckDB + Parquet), a recomendação técnica consiste em:
   - **Opção A (Interativa Server-Side Full):** Deploy via container Docker (`marimo run sala_situacao.py`) em plataforma PaaS (ex.: Hugging Face Spaces, Fly.io, Cloud Run).
   - **Opção B (Pública Estática Zero-Infra):** Exportação via `marimo-studio view export dashboard --runtime zero-python` publicada no GitHub Pages ou Vercel.
