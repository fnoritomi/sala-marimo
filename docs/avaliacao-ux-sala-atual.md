# Avaliação Crítica de UX e Visualização da Sala de Situação Atual

Esta avaliação examina criticamente cada visualização e componente da Sala de Situação legada em Pentaho CDE, aplicando princípios consolidados de Visualização de Dados (Tufte, Cleveland & McGill, Few) e Design de Interação Analítica (Shneiderman: *Overview first, zoom and filter, then details-on-demand*).

---

## 1. Avaliação Componente a Componente

### 1.1 Totalizadores / Cards de Vidas e Operadoras
1. **Qual pergunta tenta responder?**
   Qual é o volume total atual de beneficiários e de operadoras ativas no setor?
2. **O gráfico atual é adequado?**
   Parcialmente. Atualmente são blocos de texto estáticos sem contexto histórico.
3. **Existe visualização melhor?**
   Sim: **KPI Cards com Contexto Executivo**. Deve conter o número principal em destaque, variação absoluta e percentual dos últimos 12 meses (delta ▲/▼), comparativo com o mês anterior e uma micro-série temporal (*sparkline*) integrada mostrando a tendência recente.
4. **Existe informação redundante?**
   Sim. Há múltiplos números soltos para total geral, total com odonto, etc., que podem ser sintetizados de forma mais coesa.
5. **Existe informação importante sem destaque?**
   Sim: a taxa de crescimento da saúde suplementar em 12 meses não tem destaque imediato, obrigando o usuário a calcular manualmente.
6. **Existe excesso de informação?**
   Não no card em si, mas na proliferação de cartões sem hierarquia.
7. **Qual deve ser a posição na nova hierarquia?**
   **Topo absoluto da página principal (Hero Area)**, servindo de termômetro imediato do setor.
8. **Ela deve continuar existindo?**
   Sim, reformulada como KPI Card analítico com sparkline.

---

### 1.2 Gráfico de Evolução Histórica de Beneficiários
1. **Qual pergunta tenta responder?**
   Como o mercado de planos de saúde está evoluindo ao longo do tempo?
2. **O gráfico atual é adequado?**
   Não. O uso de colunas verticais para séries de 36 a 60 meses gera efeito "cerca de ripas" (*comb effect*), poluição visual e força rótulos em ângulo de 45º/90º ilegíveis.
3. **Existe visualização melhor?**
   Sim: **Gráfico de Linhas / Área Suave ECharts** com séries distintas para assistência médica e odontológica, `dataZoom` dinâmico (permitindo navegar entre 12m, 24m, 36m ou todo o histórico), marcadores discretos e tooltip enriquecido com variação mensal e anual.
4. **Existe informação redundante?**
   Repetição desnecessária de eixos em gráficos separados para médica e odonto.
5. **Existe informação importante sem destaque?**
   Falta destacar pontos de inflexão macroeconômicos e a tendência de médio prazo.
6. **Existe excesso de informação?**
   Rotulagem de todos os pontos na tela simultaneamente.
7. **Qual deve ser a posição na nova hierarquia?**
   **Primeira seção analítica logo abaixo dos KPIs**.
8. **Ela deve continuar existindo?**
   Sim, convertida em gráfico de linhas/área contínuo interativo.

---

### 1.3 Gráfico de Tipos de Contratação
1. **Qual pergunta tenta responder?**
   Qual é a participação dos planos empresariais, individuais e por adesão no mercado?
2. **O gráfico atual é adequado?**
   Não. O gráfico de pizza / donut frequentemente usado esconde proporções precisas (dificuldade do cérebro humano em comparar áreas e ângulos).
3. **Existe visualização melhor?**
   Sim: **Barras Proporcionais Empilhadas (100% Stacked Bar)** ou **Barras Horizontais Ordenadas** com percentuais claros e contagem de vidas, permitindo cross-filter com 1 clique.
4. **Existe informação redundante?**
   Legendas duplicadas e repetição de dados em tabelas adjacentes.
5. **Existe informação importante sem destaque?**
   O encolhimento histórico da carteira individual/familiar em relação ao avanço dos planos corporativos não fica evidente na pizza estática.
6. **Existe excesso de informação?**
   Não excesso de categorias (são 3), mas formato ineficiente.
7. **Qual deve ser a posição na nova hierarquia?**
   Seção **Perfil do Setor** (lado a lado com Modalidades).
8. **Ela deve continuar existindo?**
   Sim, redesenhada como barras horizontais ordenadas / 100% empilhadas.

---

### 1.4 Gráfico de Modalidades de Operadoras
1. **Qual pergunta tenta responder?**
   Quais modelos de gestão e naturezas jurídicas (cooperativas, medicina de grupo, seguradoras, etc.) dominam o setor?
2. **O gráfico atual é adequado?**
   Não. Gráficos de pizza ou colunas com 7 a 9 categorias misturam fatias minúsculas (filantropia, autogestão) com fatias gigantes (cooperativas, medicina de grupo), tornando legendas confusas.
3. **Existe visualização melhor?**
   Sim: **Gráfico de Barras Horizontais Ordenadas** em ordem decrescente de vidas, com indicação de participação percentual (%) e total de beneficiários, permitindo leitura direta dos nomes sem rotação.
4. **Existe informação redundante?**
   Sim, dados repetidos em tabelas de apoio estáticas.
5. **Existe informação importante sem destaque?**
   A perda de participação de certas modalidades e o ganho de medicina de grupo corporativa.
6. **Existe excesso de informação?**
   Categorias residuais sem agrupamento adequado.
7. **Qual deve ser a posição na nova hierarquia?**
   Seção **Perfil do Setor**.
8. **Ela deve continuar existindo?**
   Sim, como barras horizontais ordenadas.

---

### 1.5 Mapa Geográfico e Cobertura Populacional
1. **Qual pergunta tenta responder?**
   Onde os beneficiários estão concentrados no Brasil e qual é o nível de penetração da saúde privada em cada estado?
2. **O gráfico atual é adequado?**
   Parcialmente. O mapa coroplético tradicional do Pentaho é pesado, estático e não responde bem quando a pergunta do usuário é "quais são os 5 estados com maior cobertura?".
3. **Existe visualização melhor?**
   Sim: **Visualização Híbrida Comutável**:
   - `[ Mapa Interativo ECharts ]`: Visualização espacial coroplética com escala contínua e tooltip com população e vidas.
   - `[ Ranking de UFs ]`: Gráfico de barras horizontais ordenadas de todas as 27 UFs.
   - **Cross-Filter**: Clicar em qualquer estado (no mapa ou no ranking) filtra instantaneamente o painel inteiro para aquele estado.
4. **Existe informação redundante?**
   Manter mapa e tabela gigante na mesma tela sem coordenação.
5. **Existe informação importante sem destaque?**
   A enorme disparidade regional (Sudeste com >35% de cobertura vs Norte/Nordeste com <15%) precisa de indicador comparativo claro.
6. **Existe excesso de informação?**
   Renderização lenta de fronteiras sem simplificação vetorial.
7. **Qual deve ser a posição na nova hierarquia?**
   Seção **Distribuição Geográfica** na área central da tela.
8. **Ela deve continuar existindo?**
   Sim, com chaveador Mapa / Ranking e cross-filter interativo.

---

### 1.6 Painel Econômico-Financeiro (Receita x Despesa)
1. **Qual pergunta tenta responder?**
   Como está o equilíbrio econômico-financeiro das operadoras? O setor está gerando superávit ou déficit operacional?
2. **O gráfico atual é adequado?**
   Não. As receitas e despesas são exibidas em gráficos de barras separados ou tabelas contábeis complexas, impedindo a percepção imediata da margem e da sinistralidade.
3. **Existe visualização melhor?**
   Sim: **Gráfico Combinado de Duplo Eixo (Receita vs Despesa Assistencial com Linha de Sinistralidade %)**.
   - Eixo esquerdo: Barras agrupadas ou linhas de Receitas de Contraprestação e Despesas Assistenciais (R$ bilhões).
   - Eixo direito: Linha de Sinistralidade (%) com faixa de alerta (ex: acima de 85%).
4. **Existe informação redundante?**
   Exibição isolada de números contábeis que já compõem o índice de sinistralidade.
5. **Existe informação importante sem destaque?**
   O resultado operacional (lucro/prejuízo operacional) é a métrica mais crítica para a sustentabilidade e quase sempre fica soterrada em notas de rodapé.
6. **Existe excesso de informação?**
   Termos do plano de contas contábil da ANS exibidos sem tradução para linguagem analítica.
7. **Qual deve ser a posição na nova hierarquia?**
   Seção **Econômico-Financeiro** dedicada.
8. **Ela deve continuar existindo?**
   Sim, totalmente reformulado em gráfico comparativo integrado.

---

### 1.7 Demandas e Reclamações de Consumidores
1. **Qual pergunta tenta responder?**
   Qual é o volume e o perfil de insatisfação dos consumidores, e quão eficaz é a resolução preliminar (NIP)?
2. **O gráfico atual é adequado?**
   Não. O número bruto de reclamações sem ponderação pela base de clientes distorce a realidade (grandes operadoras sempre parecem piores apenas pelo porte).
3. **Existe visualização melhor?**
   Sim: **Série Temporal de Demandas por 10.000 Beneficiários** (taxa normalizada) acompanhada de:
   - Decomposição percentual: Demandas Assistenciais (negativa de cobertura, rol, prazos) vs Não Assistenciais (reajustes, contratos).
   - Indicador de Taxa de Resolutividade Prévia da NIP (%).
4. **Existe informação redundante?**
   Listagem crua de protocolos sem agregação analítica.
5. **Existe informação importante sem destaque?**
   O percentual de problemas resolvidos antes de virar processo sancionador.
6. **Existe excesso de informação?**
   Detalhamento de dezenas de subtemas na tela inicial.
7. **Qual deve ser a posição na nova hierarquia?**
   Seção **Experiência do Consumidor**.
8. **Ela deve continuar existindo?**
   Sim, com métricas normalizadas por 10k vidas.

---

### 1.8 Tabela de Operadoras e Planos
1. **Qual pergunta tenta responder?**
   Quem são as maiores operadoras do setor e como cada uma se posiciona em vidas, sinistralidade e reclamações?
2. **O gráfico atual é adequado?**
   Não. É uma tabela estática longa, com dezenas de colunas condensadas e paginação lenta.
3. **Existe visualização melhor?**
   Sim: **Tabela Analítica Top Operadoras com Busca e Drill-through**:
   - Ranking das operadoras por número de beneficiários (estoque).
   - Colunas essenciais: Operadora (Razão Social / Nome Fantasia), Modalidade, Vidas, Participação de Mercado (%), Sinistralidade Recente e IGR.
   - Campo de busca instantânea com filtro no browser.
   - Ação de clique para drill-through no perfil específico da operadora.
4. **Existe informação redundante?**
   Exibição simultânea de Razão Social, CNPJ, Registro ANS e endereço na mesma linha.
5. **Existe informação importante sem destaque?**
   A concentração de mercado (market share) das operadoras líderes.
6. **Existe excesso de informação?**
   Sim, excesso de campos cadastrais numa visão de setor.
7. **Qual deve ser a posição na nova hierarquia?**
   Seção final da página principal (**Visão de Operadoras e Mercado**).
8. **Ela deve continuar existindo?**
   Sim, simplificada e com recursos de ordenação e busca rápida.
