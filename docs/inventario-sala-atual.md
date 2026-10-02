# Inventário da Sala de Situação Atual da ANS (Pentaho CDE)

Este documento registra o inventário funcional completo da Sala de Situação da Agência Nacional de Saúde Suplementar (ANS), baseando-se no dashboard Pentaho (`Perfil do Setor.wcdf`), no *Manual da Sala de Situação da ANS: Conceitos e Fontes de Dados*, e no ecossistema de dados abertos e tabulações (SIB, DIOPS, NIP, CADOP).

---

## 1. Mapeamento de Componentes e Métricas

| Página | Componente | Métrica | Dimensões | Filtros | Visual atual | Observação |
|---|---|---|---|---|---|---|
| **Setor** | Totalizadores de Beneficiários | Total de Vidas Ativas | Tipo de Assistência (Médica / Odontológica) | Competência, UF, Modalidade, Contratação | Cards HTML simples com texto | Exibe número estático sem variação (delta) temporal nem indicador contextual |
| **Setor** | Evolução Histórica de Beneficiários | Número de Beneficiários (Estoque mensal) | Tempo (Mês/Ano), Tipo de Cobertura Assistencial | Período (anos/meses), UF, Modalidade, Tipo de Contratação | Gráfico de barras verticais densas ou linhas CCC | Difícil leitura em horizontes longos (36+ meses); rótulos do eixo X sobrepostos |
| **Setor** | Perfil por Tipo de Contratação | Beneficiários por Contratação | Tipo de Contratação (Coletivo Empresarial, Individual/Familiar, Coletivo por Adesão) | Competência, UF, Modalidade | Gráfico de Pizza / Donut fatiado | Dificulta comparação percentual precisa entre fatias similares |
| **Setor** | Perfil por Modalidade de Operadora | Beneficiários por Modalidade | Modalidade jurídica (Cooperativa médica, Medicina de grupo, Autogestão, Seguradora, Filantropia, etc.) | Competência, UF, Contratação, Assistência | Gráfico de barras verticais ou pizza com muitas categorias | Categorias com valores pequenos ficam ilegíveis ou espremidas na legenda |
| **Setor** | Distribuição Geográfica | Beneficiários por UF e Região | Região, Unidade da Federação (UF) | Competência, Assistência, Contratação, Modalidade | Mapa coroplético do Brasil (Flash/SVG legado) e tabela estática | Não permite cross-filter com outros gráficos ao clicar em uma UF |
| **Setor** | Taxa de Cobertura Populacional | Razão Beneficiários / População IBGE (%) | UF, Região | Competência, Tipo de Assistência | Tabela / Mapa com escala de cor | Sem ranking ordenado explícito; dificulta identificar os estados de menor/maior cobertura |
| **Setor** | Pirâmide Etária / Faixas Etárias | Beneficiários por Faixa Etária e Sexo | Faixa Etária (10 faixas da RN 63/2003: 0-18 até 59+), Sexo | Competência, UF, Modalidade, Contratação | Gráfico de barras bidirecionais (pirâmide) | Eixo central frequentemente desalinhado e sem destaque para envelhecimento da carteira |
| **Setor** | Operadoras Ativas | Contagem de Operadoras | Situação de Registro (com ou sem beneficiários), Porte (Pequeno, Médio, Grande) | Competência, Modalidade, UF de Sede | Cartões numéricos e tabela simples | Mistura operadoras ativas com beneficiários e ativas sem movimentação |
| **Setor** | Planos de Saúde | Quantidade de Planos Registrados | Situação de Comercialização (Ativo, Suspenso, Cancelado), Contratação | Competência, Modalidade, Tipo de Assistência | Tabela estática resumida | Alta cardinalidade sem filtros de pesquisa eficientes |
| **Setor** | Panorama Econômico-Financeiro | Receita de Contraprestações (R$) e Despesas Assistenciais (R$) | Tempo (Trimestre/Ano), Modalidade, Porte | Competência/Exercício, Modalidade, Porte | Gráficos de barras agrupadas independentes | Não evidencia diretamente a sinistralidade (Despesa / Receita) nem o resultado operacional |
| **Setor** | Sinistralidade do Setor | Índice de Sinistralidade (%) = (Despesas Assistenciais / Contraprestações) * 100 | Trimestre, Modalidade | Exercício/Ano, Modalidade | Linha com marcadores ou coluna | Frequentemente exibida separada dos valores absolutos de receita e despesa |
| **Setor** | Demandas dos Consumidores | Volume de Reclamações e NIPs (Notificação de Intermediação Preliminar) | Tempo (Mês/Ano), Natureza da Demanda (Assistencial vs Não Assistencial) | Período, UF, Modalidade | Gráfico de colunas empilhadas | Não calcula taxa de demandas ponderada por 10.000 beneficiários na visão setorial |
| **Setor** | Resolutividade de Demandas | Taxa de Resolução Prévia de Demandas (%) | Tema da Demanda (Prazos, Cobertura, Reajuste), Natureza | Período, Modalidade | Tabela de porcentagens | Sem destaque visual para temas com pior resolutividade |
| **Operadoras** | Cadastro e Porte da Operadora | Registro ANS, Razão Social, Nome Fantasia, CNPJ, Modalidade, Porte, UF sede | Registro ANS | Busca por Registro ANS ou Razão Social | Painel textual / Formulário estático | Busca textual lenta em listas longas; sem autocomplete moderno |
| **Operadoras** | Histórico de Beneficiários da Operadora | Vidas da Operadora no Tempo | Tempo (Mês/Ano), Segmentação Assistencial, Contratação | Registro ANS, Período | Gráfico de linha temporal simples | Não compara a evolução da operadora com o benchmark médio do setor ou do mesmo porte |
| **Operadoras** | Indicadores Financeiros da Operadora | Receitas, Sinistralidade, Margem de Lucro Líquida | Trimestre / Exercício contábil (DIOPS) | Registro ANS, Exercício | Tabela contábil paginada | Excesso de termos contábeis densos sem síntese visual executiva |
| **Operadoras** | Indicador de Reclamações (IGR) | IGR (Índice Geral de Reclamações por 10 mil vidas) e Ranking | Período (mês/trimestre), Porte | Registro ANS, Período | Tabela comparativa por faixa de porte | Falta visualização de dispersão (Scatter plot) entre tamanho e reclamações |
| **Operadoras** | Desempenho no IDSS | Pontuação Geral do IDSS (0,00 a 1,00) e Dimensões (Qualidade, Acesso, Sustentabilidade, Processos) | Ano-base de Avaliação, Dimensão IDSS | Registro ANS, Ano | Gráfico radar ou barras horizontais | Dificuldade para acompanhar evolução histórica das dimensões ao longo dos anos |

---

## 2. Dimensões Analíticas e Hierarquias

### 2.1 Dimensão Geográfica
- **País**: Brasil
  - **Região**: Norte, Nordeste, Sudeste, Sul, Centro-Oeste
    - **UF**: 27 Unidades da Federação (AC, AL, AM, AP, BA, CE, DF, ES, GO, MA, MG, MS, MT, PA, PB, PE, PI, PR, RJ, RN, RO, RR, RS, SC, SE, SP, TO)
      - **Município**: Código IBGE (disponível em dados granulares)

### 2.2 Dimensão Temporal
- **Ano**: Ex. 2022 a 2026
  - **Trimestre**: Q1, Q2, Q3, Q4 (utilizado prioritariamente no DIOPS contábil)
    - **Competência Mensal**: YYYY-MM (mês de referência do SIB e NIP)

### 2.3 Segmentação Assistencial
- **Médico-hospitalar**: Planos com cobertura ambulatorial, hospitalar com ou sem obstetrícia (podendo incluir odontologia agregada).
- **Exclusivamente Odontológico**: Planos restritos à assistência odontológica.

### 2.4 Tipo de Contratação
- **Coletivo Empresarial**: Vinculado a empregador pessoa jurídica.
- **Individual ou Familiar**: Contratação direta por pessoa física.
- **Coletivo por Adesão**: Vinculado a entidades de classe, sindicatos ou associações.

### 2.5 Modalidade da Operadora
- Cooperativa médica
- Medicina de grupo
- Seguradora especializada em saúde
- Autogestão (patrocinada e não patrocinada)
- Filantropia
- Cooperativa odontológica
- Odontologia de grupo

### 2.6 Faixas Etárias Oficiais (RN 63/2003)
- 0 a 18 anos
- 19 a 23 anos
- 24 a 28 anos
- 29 a 33 anos
- 34 a 38 anos
- 39 a 43 anos
- 44 a 48 anos
- 49 a 53 anos
- 54 a 58 anos
- 59 anos ou mais

---

## 3. Fontes de Dados Oficiais da ANS

1. **SIB (Sistema de Informações de Beneficiários)**: Cadastro individual de vínculos de beneficiários enviados mensalmente pelas operadoras. Base para dimensionamento de vidas ativas e movimentações (inclusões/cancelamentos).
2. **DIOPS (Documento de Informações Periódicas das Operadoras)**: Informações contábeis e financeiras enviadas trimestralmente pelas operadoras à Diretoria de Normas e Habilitação das Operadoras (DIOPE).
3. **NIP (Notificação de Intermediação Preliminar)**: Sistema de registro e acompanhamento de reclamações de consumidores, mediação com as operadoras e cálculo do IGR.
4. **CADOP (Cadastro de Operadoras)**: Dados cadastrais, modalidade jurídica, situação de funcionamento, registro de diretores e endereços.
5. **RPS (Registro de Planos de Saúde)**: Dados dos produtos e planos comercializados, segmentação assistencial e rede conveniada.
6. **Estimativas Populacionais IBGE**: Dados demográficos anuais utilizados para cálculo das taxas de cobertura da saúde suplementar.
