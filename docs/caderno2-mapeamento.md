# Mapeamento Funcional: Caderno 2.0 (Cubo de Beneficiários) da ANS vs. Parquet Moderno

**Data de Elaboração:** Outubro de 2026  
**Fonte de Dados Analisada:** `https://pub-48d2d8006ad24ec78c704a7650702ac7.r2.dev/beneficiarios/bene_2022-rg8m.parquet`  
**Referência Metodológica:** Sala de Situação da ANS — Caderno 2.0 (Cubo de Beneficiários - Sistema Legado Pentaho/Saiku)

---

## 1. Visão Geral do Caderno 2.0 Legado

O **Caderno 2.0 — Cubo de Beneficiários** era uma das ferramentas analíticas mais consultadas da antiga Sala de Situação da ANS. Ele operava sobre uma engine OLAP (Mondrian / Pentaho Saiku) que permitia cruzamentos multidimensionais livres de beneficiários por tempo, características cadastrais, localização geográfica, tipo de contratação e dados da operadora.

Apesar de seu grande poder analítico, o Caderno 2.0 apresentava importantes gargalos de usabilidade e confiabilidade:
1. **Interface Rígida (Saiku):** Exigia que o usuário compreendesse conceitos abstratos de cubos OLAP (fatos, dimensões, hierarquias, membros e tuplas).
2. **Risco Crítico de Agregação Indevida:** A quantidade de beneficiários é uma **medida semi-aditiva (snapshot temporal)**. Usuários sem treinamento técnico frequentemente somavam dados de múltiplos meses, gerando números irreais (por exemplo, 951 milhões de vidas no ano em vez de ~80 milhões).
3. **Lentidão em Consultas Complexas:** Consultas com múltiplas dimensões e alta cardinalidade (ex.: municípios ou operadoras) causavam lentidão extrema ou travamento da sessão no servidor Java.

---

## 2. Tabela Comparativa de Conceitos e Campos

| Conceito Caderno 2.0 | Campo Parquet (`bene_2022-rg8m`) | Tipo DuckDB | Disponível? | Observações Regulatórias e de Negócio |
|---|---|:---:|:---:|---|
| **Quantidade de Beneficiários** | `QT_ATIVOS` | `DOUBLE` | **SIM** | **Medida de estoque (snapshot mensal).** Representa o número de vidas ativas no último dia do mês de referência. Não aditiva no tempo. |
| **Quantidade de Adesões** | `QT_ADESOES` | `DOUBLE` | **SIM** | **Medida de fluxo mensal.** Representa novas inclusões de beneficiários formalizadas no mês de competência. Aditiva no tempo. |
| **Quantidade de Cancelamentos** | `QT_CANCELAMENTOS` | `DOUBLE` | **SIM** | **Medida de fluxo mensal.** Representa rescisões contratuais e exclusões no mês de competência. Aditiva no tempo. |
| **Mês Competência** | `COMPETENCIA` | `DATE` | **SIM** | Competência mensal no formato `YYYY-MM-DD` (12 meses de 2022: `2022-01-01` a `2022-12-01`). |
| **Área / UF de Residência** | `SG_UF` | `VARCHAR` | **SIM** | Sigla das 27 Unidades da Federação + categoria 'Não Identificado' (residência informada do beneficiário). |
| **Município de Residência** | `CD_MUNICIPIO` / `NM_MUNICIPIO` | `VARCHAR` | **SIM** | Código IBGE (6 dígitos) e nome textual do município de residência (5.310 municípios presentes). |
| **Sexo do Beneficiário** | `TP_SEXO` | `VARCHAR` | **SIM** | Sexo biológico cadastral: `F` (Feminino), `M` (Masculino), `Não Identificado`. |
| **Faixa Etária** | `DE_FAIXA_ETARIA` | `VARCHAR` | **SIM** | Faixa etária padrão ANS em intervalos de 5 anos (00 a 05 até 61 ou mais). Ideal para pirâmides etárias. |
| **Faixa Etária de Reajuste** | `DE_FAIXA_ETARIA_REAJ` | `VARCHAR` | **SIM** | Faixas etárias normativas definidas pela RN ANS nº 63/2003 para reajuste por variação de idade. |
| **Época de Contratação** | `TP_VIGENCIA_PLANO` | `VARCHAR` | **SIM** | Indicador de vigência em relação ao marco regulatório: `A` (Planos Antigos, pré-Lei 9.656/1998) e `P` (Planos Novos/Adaptados, pós-Lei). |
| **Tipo de Contratação** | `DE_CONTRATACAO_PLANO` | `VARCHAR` | **SIM** | Modalidade jurídica de contratação: `COLETIVO EMPRESARIAL`, `INDIVIDUAL OU FAMILIAR`, `COLETIVO POR ADESÃO`, etc. |
| **Segmentação do Plano** | `DE_SEGMENTACAO_PLANO` | `VARCHAR` | **SIM** | Amplitude da cobertura: `AMBULATORIAL`, `HOSPITALAR COM OBSTETRÍCIA`, `AMBULATORIAL + HOSPITALAR COM OBSTETRÍCIA`, etc. |
| **Abrangência Geográfica** | `DE_ABRG_GEOGRAFICA_PLANO` | `VARCHAR` | **SIM** | Cobertura territorial do plano: `NACIONAL`, `ESTADUAL`, `MUNICIPAL`, `GRUPO DE ESTADOS`, `GRUPO DE MUNICÍPIOS`. |
| **Cobertura Assistencial** | `COBERTURA_ASSIST_PLAN` | `VARCHAR` | **SIM** | Tipo de assistência: `Médico-hospitalar` ou `Odontológico`. |
| **Titularidade** | `TIPO_VINCULO` | `VARCHAR` | **SIM** | Vínculo com a operadora/contratante: `TITULAR`, `DEPENDENTE`, `Não Identificado`. |
| **Modalidade da Operadora** | `MODALIDADE_OPERADORA` | `VARCHAR` | **SIM** | Natureza institucional: `COOPERATIVA MÉDICA`, `MEDICINA DE GRUPO`, `SEGURADORA ESPECIALIZADA EM SAÚDE`, `AUTOGESTÃO`, `FILANTROPIA`, etc. |
| **Código da Operadora** | `CD_OPERADORA` | `VARCHAR` | **SIM** | Número de registro da operadora na ANS (6 dígitos com zeros à esquerda). 988 operadoras distintas. |
| **Razão Social da Operadora** | `NM_RAZAO_SOCIAL` | `VARCHAR` | **SIM** | Nome empresarial registrado da operadora de planos de saúde. |

---

## 3. Conceitos Não Disponíveis ou Ausentes no Parquet

Durante a inspeção direta da fonte de dados, confirmou-se que todos os conceitos essenciais do Caderno 2.0 estão disponíveis. As seguintes dimensões secundárias não constam nesta tabela consolidada:
- **Porte da Operadora:** No Caderno 2.0, operadoras podiam ser classificadas em Grande, Médio ou Pequeno Porte. No Parquet, essa classificação não está gravada como coluna nativa (pode ser inferida pelo volume total de beneficiários ou via join com dimensão de operadoras).
- **Rede Hospitalar Própria vs. Credenciada:** Não disponível nesta granularidade.
- **Data de Nascimento Exata:** Substituída por faixas etárias agrupadas para preservação da privacidade e aderência à LGPD.

---

## 4. Diretrizes para a Nova Experiência do Usuário

1. **Eliminar a Metáfora de Cubo OLAP Complexo:** Substituir a terminologia do Saiku por conceitos naturais: **Medida**, **Linhas**, **Colunas** e **Filtros**.
2. **Automatização da Semi-Aditividade:** Proteger ativamente o usuário contra cálculos incorretos. A aplicação assume a última competência selecionada como referência quando o tempo não estiver nas linhas/colunas.
3. **Transparência Analítica:** Disponibilizar uma aba de "Definições" explicando a metodologia da métrica e uma aba "Ver SQL" para fins de auditoria e validação por usuários técnicos.
