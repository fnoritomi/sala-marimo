# Justificativas do Redesign: Sala Pentaho Legada vs Nova Sala Moderna

Este documento sintetiza as decisões de design, visualização e experiência do usuário que justificam a reformulação da Sala de Situação da ANS. A semântica e a metodologia de cálculo das métricas oficiais da ANS foram rigorosamente mantidas.

---

## 1. Tabela de Transformações Visuais e Analíticas

| Informação | Solução Atual (Pentaho) | Nova Solução (Svelte + ECharts) | Motivo |
|---|---|---|---|
| **Total de Beneficiários e Operadoras** | Bloco de texto simples sem variação temporal | KPI Cards executivos com número principal, delta de 12 meses (▲/▼), texto de apoio e micro sparkline | Responde imediatamente à pergunta de relevância no topo ("O que mudou recentemente?"); evita números isolados sem contexto histórico |
| **Evolução Temporal de Beneficiários** | Colunas verticais densas ou linhas estáticas com eixos sobrepostos | Gráfico contínuo de linhas/áreas com `dataZoom`, seletores de corte temporal (12m, 24m, 36m, tudo) e marcadores dinâmicos | Elimina o "efeito cerca de ripas" em séries longas (36+ meses), melhora a legibilidade dos rótulos de data e permite zoom fluido |
| **Composição por Tipo de Contratação** | Gráfico de Pizza / Donut fatiado | Barras horizontais proporcionais empilhadas 100% (ou barras horizontais ordenadas) com percentual e vidas | Estudos de percepção visual comprovam que o olho humano compara comprimentos em eixos alinhados com precisão 4x superior a ângulos de pizza |
| **Distribuição por Modalidade de Operadora** | Gráfico de pizza com 8+ fatias ou colunas verticais desalinhadas | Gráfico de barras horizontais ordenadas decrescentemente com indicação de market share (%) | Permite acomodar rótulos textuais longos ("Cooperativa Médica", "Seguradora Especializada") sem rotação ou abreviações confusas |
| **Distribuição Geográfica de Vidas e Cobertura** | Mapa Flash/SVG estático isolado de tabelas | Visualização híbrida comutável: [ Mapa Coroplético ECharts ] e [ Ranking de UFs Ordenado ] com cross-filter | O mapa responde "onde", mas o ranking de barras responde "quem são os maiores/menores". O chaveador atende a ambas as perguntas de forma otimizada |
| **Interação Geográfica (Cross-Filtering)** | Recarregamento total da página ao trocar UF via dropdown | Clique direto no mapa ou ranking que filtra o painel inteiro via store reativo local com chip de remoção no topo | Proporciona exploração sem atrito em menos de 100 ms sem recarregar o servidor a cada clique |
| **Receitas de Contraprestações vs Despesas Assistenciais** | Gráficos de barras agrupadas independentes ou tabelas contábeis | Gráfico comparativo de duplo eixo integrando Receita, Despesa e Linha de Sinistralidade (%) com zona de alerta | Evidencia diretamente a relação de sustentabilidade e a margem operacional das operadoras em uma única visualização coerente |
| **Reclamações e Demandas dos Consumidores** | Contagem bruta de reclamações em gráfico de colunas | Série temporal de taxa de demandas por 10.000 beneficiários + composição de temas + taxa de resolução NIP (%) | A métrica absoluta penaliza operadoras de grande porte; a taxa normalizada por 10k vidas reflete com justiça a qualidade percebida do serviço |
| **Ranking e Perfil de Operadoras** | Tabela contábil longa, com 20 colunas minúsculas e paginação lenta | Tabela analítica das Top 15 operadoras com campo de busca em tempo real no browser, ordenação por coluna e link para drill-through | Facilita a consulta sem sobrecarga cognitiva, focando nos 5 indicadores decisivos de cada operadora |
| **Metadados Metodológicos** | Notas de rodapé extensas ou manuais em PDF externos | Ícone contextual `[ⓘ]` em cada indicador abrindo Drawer lateral deslizante acessível | Progressive disclosure: mantém a interface visualmente limpa enquanto oferece máxima transparência para pesquisadores |
| **Exportação de Dados** | Download CSV desformatado ou inexistente para visões filtradas | Modal de download com opções CSV e Parquet gerados diretamente pelo engine DuckDB | Respeita os filtros ativos no momento do download e processa dados em alta velocidade via streaming sem travar o browser |

---

## 2. Princípios Adotados para a Reformulação

1. **Eficiência Cognitiva**: O usuário deve compreender o estado geral da saúde suplementar nos primeiros 5 segundos de leitura.
2. **Soberania do Dado Analítico**: A identidade visual é séria, discreta e funcional (tons institucionais sóbrios, fundo neutro, tipografia nítida, paleta semântica acessível).
3. **Desacoplamento de Computação**: Cálculos e filtros locais que operam sobre os dados já carregados no cliente ocorrem instantaneamente no browser; novas agregações de grande porte recorrem ao DuckDB via marimo.
