# Registro de Dúvidas, Premissas e Regras de Negócio Validadas

Este documento cataloga as regras de negócio canônicas da ANS, premissas metodológicas adotadas na reimplementação da Sala de Situação e pontos que devem ser validados formalmente com a equipe técnica/atuarial da ANS caso haja evolução regulatória.

---

## 1. Regras de Negócio Canônicas Implementadas

### 1.1 Medida de Estoque (Semi-Aditiva) de Beneficiários
- **Conceito Oficial ANS**: O quantitativo de beneficiários reflete a posição de vínculos ativos no último dia da competência mensal (dados provenientes do SIB).
- **Regra de Agregação Temporal**:
  - Quando a visão analítica abrange um período de tempo (ex.: ano fechado, trimestre, intervalo customizado), o valor consolidado de beneficiários é **estritamente o estoque da última competência válida do intervalo** (`LAST_VALUE` / `MAX(competencia)`).
  - É vedada a soma cumulativa (`SUM(beneficiarios)`) ao longo das competências para cálculo do estoque de vidas.
  - A variação temporal de beneficiários é calculada como:
    $$\Delta \% = \left(\frac{\text{Beneficiários}(T)}{\text{Beneficiários}(T - 12\text{ meses})} - 1\right) \times 100$$

### 1.2 Medidas Aditivas de Fluxo Econômico-Financeiro (DIOPS)
- **Conceito Oficial ANS**: Receitas de contraprestações e despesas com eventos indenizáveis/assistenciais são fluxos contábeis acumulados no trimestre/ano.
- **Regra de Agregação**:
  - Em recortes de período (trimestre, 12 meses móveis, ano), aplica-se a soma aditiva padrão (`SUM()`).
  - **Índice de Sinistralidade do Setor**:
    $$\text{Sinistralidade} (\%) = \left(\frac{\sum \text{Despesas Assistenciais}}{\sum \text{Receitas de Contraprestações}}\right) \times 100$$
  - Deve ser calculado **após** a consolidação das somas do período e dos filtros aplicados, e nunca pela média aritmética de sinistralidades pré-calculadas.

### 1.3 Segmentação Assistencial (Exclusividade)
- A classificação assistencial no SIB divide os produtos e vínculos em:
  1. **Médico-Hospitalar** (ambulatorial, hospitalar com ou sem obstetrícia, com odontologia agregada ou não).
  2. **Exclusivamente Odontológico** (planos estritamente odontológicos).
- Vidas em planos exclusivamente odontológicos e vidas médico-hospitalares são contabilizadas separadamente ou em métricas claramente identificadas, pois uma mesma pessoa física pode possuir simultaneamente um plano médico e um plano odontológico independente.

### 1.4 Taxa de Cobertura da População (%)
- Indicador oficial que relaciona o total de beneficiários de planos médico-hospitalares residentes na UF com a população estimada pelo IBGE para a mesma competência/ano:
  $$\text{Taxa de Cobertura UF} (\%) = \left(\frac{\text{Beneficiários Residentes na UF}}{\text{População IBGE da UF}}\right) \times 100$$

### 1.5 Demandas e Notificação de Intermediação Preliminar (NIP)
- A NIP busca resolver conflitos entre consumidor e operadora antes da instauração de processo administrativo sancionador.
- **Taxa de Demandas**: Calculada por 10.000 beneficiários:
  $$\text{Taxa de Demandas / 10k} = \left(\frac{\text{Total de Demandas Registradas no Período}}{\text{Média de Beneficiários Ativos no Período}}\right) \times 10.000$$
- **Resolutividade Prévia**: Percentual de demandas concluídas com resolução voluntária pela operadora:
  $$\text{Taxa de Resolutividade} (\%) = \left(\frac{\text{Demandas Resolvidas}}{\text{Demandas Finalizadas}}\right) \times 100$$

---

## 2. Dúvidas e Itens para Validação com a ANS

| Item | Contexto Regulatório | Solução Adotada na Nova Sala | Pergunta / Ponto de Validação |
|---|---|---|---|
| **1. Alocação Geográfica de Beneficiários** | Uma operadora pode ter sede em SP, mas comercializar planos para beneficiários residentes em MG ou RJ. | Adotou-se a **UF de residência do beneficiário** como dimensão primária para análises demográficas e mapa, e **UF de sede** para a tabela cadastral de operadoras. | Confirmar se para a visão "Setor" o mapa de calor deve refletir sempre a residência do beneficiário (visão SIB) ou se há interesse em chavear para UF de registro da operadora. |
| **2. Competência DIOPS x SIB** | O SIB tem periodicidade de atualização mensal, enquanto o DIOPS contábil é trimestral (com defasagem regulatória de ~60 a 90 dias para consolidação dos balancetes). | Para visualizações mensais contínuas, os valores do DIOPS são apresentados por trimestre de competência, interpolando-se visualmente os trimestres ou exibindo no eixo o trimestre contábil de referência. | Validar se na visão integrada de finanças a série deve ser estritamente trimestral ou se a anualização móvel de 12 meses é o padrão preferido pelos analistas da agência. |
| **3. Planos com Odontologia Agregada** | Beneficiários com plano médico que contempla cobertura odontológica embutida. | São classificados no grupo **Médico-Hospitalar**, mantendo a convenção histórica dos Cadernos de Informação da ANS. | Confirmar se há necessidade de um filtro secundário específico "Com Odontologia / Sem Odontologia" dentro do grupo médico-hospitalar. |
| **4. Tratamento de Operadoras sob Regime Especial** | Operadoras em direção fiscal, técnica ou liquidação extrajudicial mantêm registro ativo temporariamente, mas com comercialização suspensa. | Na visão setorial de operadoras ativas, destacam-se operadoras **Ativas com beneficiários**. Operadoras em liquidação sem vidas são segregadas. | Validar se o filtro de operadoras deve incluir opção para visualizar operadoras sob regimes especiais de fiscalização. |
