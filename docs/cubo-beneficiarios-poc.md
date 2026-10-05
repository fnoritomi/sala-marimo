# PoC da Nova Sala de Situação da ANS: Módulo de Consulta de Beneficiários

## 1. Visão Geral e Contexto Executivo

A **Sala de Situação da Agência Nacional de Saúde Suplementar (ANS)** historicamente disponibilizou o **Caderno 2.0 / Cubo de Beneficiários** como a principal ferramenta analítica multidimensional para operadores do setor, pesquisadores e reguladores. Construído sobre tecnologias OLAP legadas (como Pentaho Mondrian e Saiku), o cubo original permitia pivotear medidas contra múltiplas dimensões regulatórias. Contudo, apresentava limitações de usabilidade, baixa performance em agregações complexas sobre bases volumosas e alta dependência de servidores centralizados e pilhas de software pesadas.

Esta Prova de Conceito (PoC) expande a aplicação **Sala de Situação da ANS em Marimo Studio**, integrando uma experiência analítica multidimensional moderna sob a arquitetura:

```text
               Navegador Web / Usuário
                         │
                         ▼
        Marimo Studio View (Svelte 5 + TypeScript)
        ┌────────────────────────────────────────┐
        │  • Interface Multidimensional Moderna  │
        │  • Seletor Semântico de Medidas        │
        │  • Linhas, Colunas (Pivot) e Filtros   │
        │  • Tabela Analítica, Gráficos & SQL    │
        └──────────────────┬─────────────────────┘
                           │ marimo reactive bridges
                           ▼
          Python Backend (`sala_situacao.py`)
        ┌────────────────────────────────────────┐
        │  • Catálogo Semântico (YAML)           │
        │  • Query Planner Parametrizado         │
        │  • Guardas de Cardinalidade            │
        │  • Regras Semi-aditivas Automáticas    │
        └──────────────────┬─────────────────────┘
                           │
                           ▼
              DuckDB In-Memory Engine
        ┌────────────────────────────────────────┐
        │  • Leitura Parquet Remota (HTTPFS)     │
        │  • Pushdown de Projeção e Predicados   │
        │  • Suporte a Cache Local Transparente  │
        └──────────────────┬─────────────────────┘
                           │ HTTP Range Requests (GET bytes=...)
                           ▼
           Cloudflare R2 Public Storage
        `bene_2022-rg8m.parquet` (81.272.978 linhas, 246.8 MB)
```

A solução elimina a necessidade de carregar 81 milhões de registros na memória do navegador ou do Python via Pandas, transferindo apenas bytes estritamente necessários via requisições por intervalo (`HTTP Range Requests`) e agregando bilhões de combinações em milissegundos.

---

## 2. Inspecionamento e Profiling da Base Parquet

A inspeção direta com DuckDB sobre o arquivo Parquet remoto `https://pub-48d2d8006ad24ec78c704a7650702ac7.r2.dev/beneficiarios/bene_2022-rg8m.parquet` revelou os seguintes dados fundamentais:

- **Tamanho Físico Remoto:** 246,8 MB (258.784.811 bytes), compactado com Snappy/ZSTD.
- **Volume de Registros:** **81.272.978 linhas**.
- **Período Coberto:** Ano de 2022 completo (12 competências mensais: `2022-01-01` a `2022-12-01`).
- **Completude:** **0 valores nulos** nas 19 colunas do arquivo.

### Resumo do Profiling por Coluna

| Campo Parquet | Tipo Físico | Distintos | Nulos | Exemplo | Papel Semântico |
|---|---|---:|---:|---|---|
| `COMPETENCIA` | DATE | 12 | 0 | `2022-12-01` | Dimensão Temporal (Partição de Snapshot) |
| `QT_ATIVOS` | BIGINT | ~8.000 | 0 | `14` | **Medida Semi-aditiva** (Snapshot de Vidas) |
| `QT_ADESOES` | BIGINT | ~1.500 | 0 | `2` | Medida Aditiva (Fluxo Mensal de Novas Vidas) |
| `QT_CANCELAMENTOS`| BIGINT | ~1.200 | 0 | `1` | Medida Aditiva (Fluxo Mensal de Evasões) |
| `SG_UF` | VARCHAR | 28 | 0 | `SP` | Dimensão Geográfica (27 UFs + Exterior) |
| `CD_MUNICIPIO` | BIGINT | 5.310 | 0 | `355030` | Código IBGE do Município |
| `NM_MUNICIPIO` | VARCHAR | 5.297 | 0 | `São Paulo` | Descrição Geográfica do Município |
| `DE_FAIXA_ETARIA`| VARCHAR | 11 | 0 | `30 a 39 anos` | Dimensão Demográfica (Faixas ANS) |
| `DE_SEXO` | VARCHAR | 2 | 0 | `F`, `M` | Dimensão Demográfica |
| `CD_OPERADORA` | BIGINT | 988 | 0 | `326305` | Registro ANS da Operadora |
| `NM_RAZAO_SOCIAL`| VARCHAR | 988 | 0 | `AMIL ASSISTÊNCIA MÉDICA...`| Dimensão de Operadora |
| `MODALIDADE` | VARCHAR | 8 | 0 | `Medicina de Grupo` | Modalidade Jurídica / Operacional |
| `DE_CONTRATACAO_PLANO`| VARCHAR | 12 | 0 | `COLETIVO EMPRESARIAL` | Tipo de Contratação |
| `DE_SEGMENTACAO` | VARCHAR | 12 | 0 | `Ambulatorial + Hospitalar com Obstetrícia` | Segmentação Assistencial do Plano |
| `DE_ABRANGENCIA` | VARCHAR | 5 | 0 | `Nacional`, `Estadual`, `Municipal` | Abrangência Geográfica do Plano |
| `COBERTURA` | VARCHAR | 2 | 0 | `Médico-hospitalar`, `Odontológico` | Cobertura Assistencial Agregada |
| `DE_VINCULO` | VARCHAR | 2 | 0 | `Titular`, `Dependente` | Condição de Titularidade |
| `ANO` | BIGINT | 1 | 0 | `2022` | Partição Temporal de Ano |
| `MES` | BIGINT | 12 | 0 | `1` a `12` | Dimensão Temporal Mensal |

Documento de profiling detalhado: [`docs/beneficiarios-parquet-profile.md`](file:///home/noritomi/sala-marimo/docs/beneficiarios-parquet-profile.md).

---

## 3. Mapeamento Funcional: Caderno 2.0 vs. Base Parquet

Diferente do Saiku legado, onde dimensões e medidas eram mapeadas estaticamente em esquemas XML Mondrian sobre bancos relacionais, na nova arquitetura estabelecemos um mapeamento semântico dinâmico em YAML ([`semantic/beneficiarios.yaml`](file:///home/noritomi/sala-marimo/semantic/beneficiarios.yaml)).

### Mapeamento das Medidas

1. **Quantidade de Beneficiários Ativos (`QT_ATIVOS`):**
   - *Status:* **Disponível nativamente.**
   - *Natureza:* **Semi-aditiva.** Representa o estoque instantâneo de pessoas cobertas em cada mês.
   - *Regra semântica:* Se a dimensão temporal (`competencia`) estiver nas linhas ou colunas, calcula-se `SUM(QT_ATIVOS)` para detalhar cada mês. Se o usuário agrupar apenas por dimensões atemporais (ex: UF, Sexo, Faixa Etária, Modalidade), o query planner injeta automaticamente o predicado `WHERE COMPETENCIA = '2022-12-01'` (snapshot mais recente). Isso impede a armadilha analítica de somar 12 meses (que totalizaria falsamente ~951 milhões de beneficiários em vez dos 80,9 milhões reais).

2. **Quantidade de Adesões (`QT_ADESOES`):**
   - *Status:* **Disponível nativamente.**
   - *Natureza:* **Aditiva.** Representa o fluxo mensal de novos contratos/vidas. Pode ser livremente agregada tanto no espaço quanto no tempo (ex: Total de adesões no 1º semestre de 2022).

3. **Quantidade de Cancelamentos (`QT_CANCELAMENTOS`):**
   - *Status:* **Disponível nativamente.**
   - *Natureza:* **Aditiva.** Representa o fluxo mensal de evasões/cancelamentos. Não foi derivada nem estimada; é auditada e reportada diretamente pelas operadoras.

### Mapeamento das Dimensões

| Conceito Original do Caderno 2.0 | Campo Parquet | Disponível? | Tratamento e UX |
|---|---|---|---|
| **Mês Competência** | `COMPETENCIA`, `MES`, `ANO` | Sim | Formato ISO `YYYY-MM-DD` com rótulo descritivo |
| **Área de Residência (UF / Município)** | `SG_UF`, `NM_MUNICIPIO`, `CD_MUNICIPIO` | Sim | UFs com filtro categórico rápido (28 opções); Municípios com busca sob demanda (`ILIKE`) |
| **Sexo do Beneficiário** | `DE_SEXO` | Sim | `F` e `M`, suporta pirâmide etária automática |
| **Faixa Etária** | `DE_FAIXA_ETARIA` | Sim | 11 faixas regulatórias ANS (`00 a 05 anos` até `80 anos ou mais`) |
| **Titularidade** | `DE_VINCULO` | Sim | `Titular` e `Dependente` |
| **Cobertura Assistencial** | `COBERTURA` | Sim | `Médico-hospitalar` e `Exclusivamente Odontológico` |
| **Segmentação do Plano** | `DE_SEGMENTACAO` | Sim | 12 descrições detalhadas da abrangência de serviços |
| **Tipo de Contratação** | `DE_CONTRATACAO_PLANO` | Sim | Coletivo Empresarial, Coletivo por Adesão, Individual/Familiar |
| **Abrangência Geográfica** | `DE_ABRANGENCIA` | Sim | Nacional, Estadual, Grupo de Estados, Municipal, Grupo de Municípios |
| **Operadora** | `NM_RAZAO_SOCIAL`, `CD_OPERADORA` | Sim | 988 operadoras; busca textual assistida por digitação |
| **Modalidade da Operadora** | `MODALIDADE` | Sim | Medicina de Grupo, Cooperativa Médica, Autogestão, Filantropia, etc. |
| **Época de Contratação** | — | Não | Ausente no arquivo fornecido. Não inventada nem interpolada. Registrada como lacuna da fonte. |

Mapeamento completo: [`docs/caderno2-mapeamento.md`](file:///home/noritomi/sala-marimo/docs/caderno2-mapeamento.md).

---

## 4. O Mecanismo de Consulta: Query Planner e Semi-aditividade

A interface web não monta SQL bruto nem envia strings arbitrárias. Ela envia uma especificação semântica tipada:

```json
{
  "measure": "beneficiarios",
  "rows": ["faixa_etaria"],
  "columns": ["sexo"],
  "filters": [
    {
      "dimension": "uf",
      "operator": "in",
      "values": ["SP", "RJ", "MG"]
    }
  ]
}
```

O `QueryPlanner` ([`src/analytics/query_planner.py`](file:///home/noritomi/sala-marimo/src/analytics/query_planner.py)) recebe o objeto e realiza:

1. **Validação de Vocabulário Semântico:** Dimensões e medidas fora do catálogo geram exceção imediata, eliminando qualquer risco de SQL injection.
2. **Estimativa de Cardinalidade Pré-execução:** Calcula o produto cartesiano das cardinalidades estimadas das dimensões solicitadas. Se `estimated_groups > 150.000` (ex: cruzar 5.310 municípios com 988 operadoras sem filtro), a consulta é rejeitada preventivamente com um alerta didático orientando o usuário a adicionar filtros de UF ou operadora.
3. **Aplicação Automática de Semi-aditividade:**
   ```sql
   -- Caso a dimensão temporal não esteja presente em rows nem columns:
   WHERE COMPETENCIA = '2022-12-01'
   ```
4. **Pivoteamento SQL Nativo:** Quando colunas são especificadas, o planner gera expressões condicionais `SUM(CASE WHEN DE_SEXO = 'F' THEN QT_ATIVOS ELSE 0 END) AS "F"` agregadas em um único passe vetorial no DuckDB.
5. **Pushdown Estrito:** Apenas as colunas necessárias para o agrupamento, filtro e medida são projetadas (`SELECT SG_UF, SUM(QT_ATIVOS)...`), reduzindo a transferência de bytes via rede em mais de 85%.

---

## 5. Benchmarks de Performance: Remoto vs. Local

Foram executadas 6 consultas analíticas representativas (Q1 a Q6), comparando acesso remoto direto via HTTPS à Cloudflare R2 versus cache local:

| Consulta | Linhas Lógicas | Grupos Retornados | Remoto (Cold) | Remoto (Warm) | Cache Local (Warm) |
|---|---:|---:|---:|---:|---:|
| **Q1: Série Temporal (12 meses)** | 81.272.978 | 12 | 2,82 s | **0,39 s** | 0,09 s |
| **Q2: Distribuição por UF (Snapshot Dez)** | 81.272.978 | 28 | 4,15 s | **0,42 s** | 0,11 s |
| **Q3: Pivot Competência × Contratação** | 81.272.978 | 12 (14 colunas) | 4,88 s | **0,58 s** | 0,14 s |
| **Q4: Pirâmide Etária (Faixa × Sexo)** | 81.272.978 | 11 (2 séries) | 3,92 s | **0,41 s** | 0,10 s |
| **Q5: Agrupamento Pesado (Operadora × UF)**| 81.272.978 | 3.421 | 13,84 s | **1,28 s** | 0,88 s |
| **Q6: Consulta Filtrada (RJ, 12 meses)** | 81.272.978 | 12 | 3,60 s | **0,45 s** | 0,12 s |

Relatório completo de benchmarks: [`docs/benchmark-remote-parquet.md`](file:///home/noritomi/sala-marimo/docs/benchmark-remote-parquet.md).

### Principais Conclusões de Infraestrutura:
- O servidor Cloudflare R2 suporta `Accept-Ranges: bytes` com respostas `206 Partial Content`.
- O DuckDB faz prefetching inteligente de metadados do Parquet (footer, dictionary pages e column chunks).
- No modo remoto warm, as consultas variam entre **390 ms e 1,28 s** para escanear 81,2 milhões de linhas. No cache local em SSD, a latência cai para **90 a 140 ms**.

---

## 6. A Nova Experiência do Usuário (Frontend Svelte 5)

A interface analítica substitui completamente os menus cinzentos e lentos do Saiku/Pentaho por um design limpo, responsivo e centrado na autonomia do usuário:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  [ Visão do Setor ]   [ ★ Explorar Beneficiários ]            Competência: 2022-12  │
├─────────────────────────────────────────────────────────────────────────────┤
│  MÉTRICA / MEDIDA:                                                          │
│  (●) Beneficiários Ativos [Estoque]   ( ) Adesões [Fluxo]   ( ) Cancelamentos [Fluxo]│
│                                                                             │
│  LINHAS:                                COLUNAS (PIVOT):                    │
│  [ Faixa Etária ✕ ] [ + Adicionar ]      [ Sexo ✕ ] [ + Adicionar ]          │
│                                                                             │
│  FILTROS RESTRITIVOS:                                                       │
│  [ UF: SP, RJ ✕ ]   [ + Adicionar Filtro ]                                  │
│                                                                             │
│  MODELOS RÁPIDOS: [Pirâmide Etária] [Evolução Contratação] [Ranking UFs]   │
│                                           [  EXECUTAR CONSULTA  ]           │
├─────────────────────────────────────────────────────────────────────────────┤
│  Abas: [ ▦ Tabela Analítica ] [ 📈 Visualização ] [ ℹ Definições Semânticas ] [ ⚙ SQL ] │
│                                                                             │
│  (Exibição dinâmica: Tabela zebrada com ordenação, exportação CSV/Parquet,   │
│   gráfico inteligente adaptativo e inspetor do SQL compilado)               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Recursos de Usabilidade Implementados:
1. **Modelos Prontos (Quick Templates):** 5 consultas comuns acessíveis com um clique (Pirâmide Etária, Série Mensal, Pivot de Contratação, Modalidade de Operadoras, Concentração Geográfica).
2. **Reordenação e Movimentação:** Botões intuitivos `⇄ Mover para Colunas` / `⇄ Mover para Linhas` em cada chip, permitindo rearranjar o cubo sem esforço.
3. **Busca e Categorização de Dimensões:** Modal com abas por domínio (`Tempo`, `Beneficiário`, `Localização`, `Plano`, `Operadora`) e busca por texto em tempo real.
4. **Filtros com Valores Sob Demanda:** Dimensões categóricas exibem lista de checkboxes pesquisável; dimensões de alta cardinalidade (`Operadora`, `Município`) oferecem busca textual indexada com `ILIKE` em DuckDB.
5. **Gráficos Inteligentes Auto-detectados:**
   - Detecta *Faixa Etária + Sexo* -> Desenha **Pirâmide Etária Bipolar** (Homens vs. Mulheres).
   - Detecta *UF única* -> Desenha **Mapa Coroplético do Brasil**.
   - Detecta *Competência* -> Desenha **Evolução Temporal em Linha / Área**.
   - Detecta *Múltiplas categorias / Pivot* -> Desenha **Barras Agrupadas / Empilhadas**.
6. **Download Direto:** Botões para exportar tanto para **CSV** formatado quanto para **Parquet** colunar otimizado.
7. **Transparência Regulatória:** A aba *Definições Semânticas* explica em linguagem natural ao usuário se foi aplicada a regra semi-aditiva, qual competência foi fixada e qual o conceito técnico da métrica.

---

## 7. Limitações Conhecidas e Recomendações Futuras

1. **Escopo Temporal:** O Parquet analisado cobre exclusivamente o ano de 2022. Para produzir séries históricas longas (ex: 2015–2026), recomenda-se particionar o dataset no storage por `ANO` e `MES` em estrutura Hive (`bene/ano=2022/mes=12/data.parquet`), permitindo que o DuckDB ignore completamente os arquivos fora do intervalo filtrado (*partition pruning*).
2. **Valores Nulos:** A base fornecida possui 0 nulos. Caso sejam adicionadas bases com registros inconsistentes, o query planner já inclui tratamento com `COALESCE` e `CASE WHEN`.
3. **WebAssembly no Navegador (DuckDB-Wasm):** Atualmente o DuckDB roda no backend Python do Marimo e transmite os dados resumidos (JSON) para o Svelte. Uma evolução futura interessante seria avaliar o DuckDB compilado em WebAssembly diretamente no cliente, permitindo consultas offline sobre o Parquet remoto sem sobrecarregar o container do servidor.
