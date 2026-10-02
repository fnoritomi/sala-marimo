# Sala de Situação da ANS - Nova Geração

Reimplementação moderna da **Sala de Situação da Agência Nacional de Saúde Suplementar (ANS)** baseada em **marimo**, **marimo-studio**, **DuckDB**, **Parquet**, **Svelte 5 + TypeScript** e **Apache ECharts**.

---

## 📚 Documentação do Projeto

Toda a engenharia reversa, análise crítica, arquitetura e decisões de design estão documentadas em detalhes:

1. [**Inventário da Sala Atual**](docs/inventario-sala-atual.md): Mapeamento exaustivo de páginas, abas, indicadores, filtros, dimensões e endpoints do Pentaho legado.
2. [**Avaliação Crítica de UX e Visualização**](docs/avaliacao-ux-sala-atual.md): Análise das 8 perguntas analíticas para cada componente legado e justificativa de substituições visuais.
3. [**Nova Arquitetura de Informação**](docs/nova-arquitetura-informacao.md): Reorganização analítica em torno das 7 perguntas de negócio da Saúde Suplementar.
4. [**Decisões de Redesign e Interação**](docs/redesign.md): Matriz de melhorias, novos gráficos ECharts, microinterações e cross-filtering.
5. [**Regras de Negócio e Dúvidas Regulatórias**](docs/duvidas-regras-negocio.md): Formalização de medidas semi-aditivas (snapshot temporal de vidas), sinistralidade, NIP/10k vidas e catálogo de dúvidas.
6. [**Arquitetura Técnica, Benchmarks e Comparativo com Dash**](docs/arquitetura-tecnica-e-benchmarks.md): Modelagem de dados, latência, testes de concorrência com 1 a 100 sessões e confronto com arquitetura tradicional baseada em callbacks no servidor.

---

## 🛠️ Stack Tecnológica

- **Storage & Ingestion:** Arquivos Parquet particionados (`ano=YYYY/mes=MM`) com compressão ZSTD.
- **Camada Semântica & Analytics Engine:** [DuckDB](https://duckdb.org/) executando agregações vetoriais com pushdown de predicados e cursores thread-safe.
- **Runtime Reativo em Python:** [marimo](https://marimo.io/) com grafo de dependências DAG e projeção de estado tipado.
- **Custom View & Frontend:** [marimo-studio](https://github.com/marimo-team/marimo-studio) integrando **Svelte 5**, **TypeScript**, **Tailwind CSS** e **Apache ECharts 5**.
- **Ambiente & Pacotes:** Python 3.12 gerenciado via [uv](https://github.com/astral-sh/uv) e frontend via Deno.

---

## 🚀 Como Executar

### 1. Pré-requisitos
- Python >= 3.12
- [uv](https://github.com/astral-sh/uv) instalado no sistema

### 2. Instalação de Dependências
```bash
uv sync
```

### 3. Geração dos Dados Sintéticos
Geração rápida para desenvolvimento (perfil dev):
```bash
uv run python scripts/generate_synthetic_data.py --profile dev
```

Geração para testes de carga e volume realista (milhões de registros, distribuição Zipf de operadoras e pesos IBGE das 27 UFs):
```bash
uv run python scripts/generate_synthetic_data.py --profile realistic --output data_realistic
```

### 4. Execução dos Testes Automatizados (pytest)
Garante invariantes metodológicas da ANS (medidas semi-aditivas, consistência de dimensões, integridade dos 27 estados e ausência de valores negativos):
```bash
uv run pytest
```

### 5. Benchmarks de Desempenho e Concorrência
Benchmark de latência analítica do DuckDB:
```bash
uv run python scripts/benchmark_duckdb.py
```

Benchmark de escalabilidade e memória (1, 10, 25, 50, 100 sessões simultâneas):
```bash
uv run python scripts/benchmark_concurrency.py --data-dir data --requests 30
```

### 6. Compilação e Operação da View Customizada (marimo-studio)
Validar e inspecionar os bindings do notebook com a view Svelte:
```bash
uv run marimo-studio validate --target sala_situacao.py
```

Compilar os componentes Svelte/TypeScript da view para produção/desenvolvimento:
```bash
uv run marimo-studio view build dashboard --target sala_situacao.py
```

Executar a aplicação interativa:
```bash
uv run marimo run sala_situacao.py
```
Ou em modo de edição e desenvolvimento visual:
```bash
uv run marimo edit sala_situacao.py
```

---

## 💡 Destaques de UX e Interatividade

- **Cross-Filter Instantâneo no Navegador:** Selecionar uma Unidade da Federação no mapa vetorial ou no ranking atualiza instantaneamente todos os demais cards e séries temporais via Svelte Store local, sem necessidade de round-trip de rede para o servidor Python.
- **Gráficos ECharts Especializados:**
  - *Série Histórica Contínua* com separação de Assistência Médica e Odontológica, zoom dinâmico e anotação regulatória.
  - *Mapa Coroplético do Brasil* com taxa de cobertura da Saúde Suplementar por população do IBGE.
  - *Gráfico de Balanço Econômico-Financeiro* com barras pareadas (Receitas vs. Despesas) e curva de Sinistralidade (%).
  - *Monitor de Demanda dos Consumidores* com volume mensal de NIPs, taxa de resolutividade e ranking por tema/natureza.
  - *Tabela Analítica Top Operadoras* com indicadores de sinistralidade, porte, UF sede e taxa NIP por 10k vidas.
- **Drawer de Metadados e Metodologia:** Painel lateral acessível exibindo fontes de dados públicas, notas regulatórias, conceitos de estoques e fluxos.
- **Modal de Exportação Streaming:** Download direto via streaming de DuckDB em formatos CSV ou Parquet ZSTD, além de exportação de gráficos em alta resolução (PNG).
