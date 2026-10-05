# Profiling Analítico: Parquet de Beneficiários da ANS (`bene_2022-rg8m.parquet`)

**Data de Análise:** Outubro de 2026  
**Localização Remota:** `https://pub-48d2d8006ad24ec78c704a7650702ac7.r2.dev/beneficiarios/bene_2022-rg8m.parquet`  
**Engine de Profiling:** DuckDB 1.2+  
**Volume Total de Registros:** 81.272.978 linhas  
**Tamanho do Arquivo:** 246.829.617 bytes (~246,8 MB)  
**Suporte a HTTP Range Requests:** Sim (`Accept-Ranges: bytes`)

---

## 1. Tabela Estrutural de Profiling

| Campo | Tipo DuckDB | Distintos Aprox. | Nulos | Exemplo Real | Classificação Semântica |
|---|:---:|---:|---:|---|---|
| `COMPETENCIA` | `DATE` | 12 | 0 | `2022-01-01` | **Data / Competência Temporal** |
| `CD_OPERADORA` | `VARCHAR` | 988 | 0 | `'006246'` | **Código / Chave de Negócio** |
| `NM_RAZAO_SOCIAL` | `VARCHAR` | 988 | 0 | `'SUL AMERICA COMPANHIA DE SEGURO SAÚDE'` | **Descrição / Dimensão (Operadora)** |
| `MODALIDADE_OPERADORA` | `VARCHAR` | 7 | 0 | `'SEGURADORA ESPECIALIZADA EM SAÚDE'` | **Dimensão Categórica (Operadora)** |
| `SG_UF` | `VARCHAR` | 28 | 0 | `'BA'` | **Dimensão Categórica (Localização)** |
| `CD_MUNICIPIO` | `VARCHAR` | 5.592 | 0 | `'291920'` | **Código IBGE (Localização)** |
| `NM_MUNICIPIO` | `VARCHAR` | 5.310 | 0 | `'LAURO DE FREITAS'` | **Descrição / Dimensão (Localização)** |
| `TP_SEXO` | `VARCHAR` | 3 | 0 | `'M'` | **Dimensão Categórica (Beneficiário)** |
| `DE_FAIXA_ETARIA` | `VARCHAR` | 14 | 0 | `'36 a 40 anos'` | **Dimensão Categórica (Beneficiário)** |
| `DE_FAIXA_ETARIA_REAJ` | `VARCHAR` | 11 | 0 | `'39 a 43 anos'` | **Dimensão Categórica (Beneficiário)** |
| `TP_VIGENCIA_PLANO` | `VARCHAR` | 2 | 0 | `'P'` | **Dimensão Categórica (Plano)** |
| `DE_CONTRATACAO_PLANO` | `VARCHAR` | 12 | 0 | `'COLETIVO EMPRESARIAL'` | **Dimensão Categórica (Plano)** |
| `DE_SEGMENTACAO_PLANO` | `VARCHAR` | 17 | 0 | `'AMBULATORIAL + HOSPITALAR COM OBSTETRÍCIA'` | **Dimensão Categórica (Plano)** |
| `DE_ABRG_GEOGRAFICA_PLANO` | `VARCHAR` | 7 | 0 | `'NACIONAL'` | **Dimensão Categórica (Plano)** |
| `COBERTURA_ASSIST_PLAN` | `VARCHAR` | 3 | 0 | `'Médico-hospitalar'` | **Dimensão Categórica (Plano)** |
| `TIPO_VINCULO` | `VARCHAR` | 3 | 0 | `'DEPENDENTE'` | **Dimensão Categórica (Beneficiário)** |
| `QT_ATIVOS` | `DOUBLE` | Contínuo | 0 | `11.0` | **Medida de Estoque (Semi-Aditiva)** |
| `QT_ADESOES` | `DOUBLE` | Contínuo | 0 | `0.0` | **Medida de Fluxo Mensal (Aditiva)** |
| `QT_CANCELAMENTOS` | `DOUBLE` | Contínuo | 0 | `1.0` | **Medida de Fluxo Mensal (Aditiva)** |

---

## 2. Estatísticas Agregadas das Medidas

As agregações calculadas sobre todas as 81,2 milhões de linhas revelam as seguintes grandezas para o exercício de 2022:

- **Soma Acumulada Bruta de `QT_ATIVOS`:** `951.533.919` vidas-mês (comprova a necessidade estrita de tratamento semi-aditivo, pois o volume real do setor gira em torno de 77 a 81 milhões de beneficiários por mês).
- **Média Mensal de Vidas Ativas:** `79.294.493` beneficiários.
- **Volume no Último Mês (`2022-12-01`):** `80.917.358` beneficiários.
- **Total Anual de Novas Adesões (`QT_ADESOES`):** `28.515.535` contratações / vidas incluídas.
- **Total Anual de Cancelamentos (`QT_CANCELAMENTOS`):** `25.268.329` rescisões / vidas excluídas.
- **Saldo Líquido Anual (Adesões - Cancelamentos):** `+3.247.206` vidas líquidas (compatível com a variação entre janeiro/2022 e dezembro/2022: de 77,6M para 80,9M vidas).

---

## 3. Classificação e Agrupamento Semântico para a Interface

Para evitar sobrecarregar o usuário e permitir consultas intuitivas, as dimensões são agrupadas em 5 eixos temáticos:

1. **TEMPO (1 dimensão):**
   - `Mês Competência` (`COMPETENCIA`): granularidade mensal em formato ISO.
2. **BENEFICIÁRIO (4 dimensões):**
   - `Sexo` (`TP_SEXO`): `F`, `M`, `Não Identificado`.
   - `Faixa Etária` (`DE_FAIXA_ETARIA`): 14 classes quinquenais.
   - `Faixa Etária Reajuste` (`DE_FAIXA_ETARIA_REAJ`): 11 classes RN 63.
   - `Titularidade` (`TIPO_VINCULO`): `TITULAR`, `DEPENDENTE`, `Não Identificado`.
3. **LOCALIZAÇÃO (2 dimensões):**
   - `UF de Residência` (`SG_UF`): 28 categorias.
   - `Município de Residência` (`NM_MUNICIPIO` / `CD_MUNICIPIO`): 5.310 municípios (alta cardinalidade, busca sob demanda).
4. **PLANO (5 dimensões):**
   - `Cobertura Assistencial` (`COBERTURA_ASSIST_PLAN`): Médico-hospitalar, Odontológico.
   - `Tipo de Contratação` (`DE_CONTRATACAO_PLANO`): Coletivo Empresarial, Individual, Coletivo por Adesão.
   - `Segmentação Assistencial` (`DE_SEGMENTACAO_PLANO`): 17 combinações ambulatoriais/hospitalares/odontológicas.
   - `Abrangência Geográfica` (`DE_ABRG_GEOGRAFICA_PLANO`): Nacional, Estadual, Municipal, Grupo de Municípios/Estados.
   - `Época de Contratação` (`TP_VIGENCIA_PLANO`): Planos Novos (`P`) vs. Planos Antigos (`A`).
5. **OPERADORA (2 dimensões):**
   - `Modalidade` (`MODALIDADE_OPERADORA`): 7 naturezas institucionais.
   - `Razão Social da Operadora` (`NM_RAZAO_SOCIAL` / `CD_OPERADORA`): 988 operadoras ativas (busca sob demanda).
