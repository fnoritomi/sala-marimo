# Pesquisa Oficial: Arquitetura, Fluxos de Publicação e Suporte no Molab / marimo

Este documento compila a investigação técnica e as referências documentais oficiais sobre o serviço hospedado **molab** (`molab.marimo.io`), o ecossistema **marimo** e a integração com **marimo-studio**.

---

## 1. O que é o Molab?

O **molab** (`https://molab.marimo.io`) é o serviço em nuvem gerenciado pela equipe oficial do **marimo**, projetado para execução, colaboração e compartilhamento de notebooks reativos em Python:

- **Infraestrutura Cloud:** Por padrão, cada notebook instanciado em servidor roda em um container com **4 vCPUs e 32 GB de RAM** (com suporte opcional a GPUs NVIDIA RTX Pro 6000 Blackwell de 96 GB VRAM).
- **Gerenciador de Pacotes:** Utiliza `uv` internamente e o gerenciador de pacotes integrado do marimo para instalação de bibliotecas sob demanda.
- **Autenticação e Sessão:** Utiliza **Clerk** como provedor de autenticação (`x-clerk-auth-status`). Sessões autenticadas podem rodar por até 12 horas (suspensão automática após 90 minutos de inatividade).
- **Modos de Visualização:**
  1. *Servidor Efêmero (Cloud Container):* Executa o kernel Python completo em ambiente Linux conteinerizado (requer login para provisionar container).
  2. *WASM / Browser Preview (`/wasm`):* Executa o notebook no navegador do visitante via **Pyodide** (acessível publicamente sem login).
  3. *Static Preview:* Exibe saídas pré-computadas salvas em `__marimo__/session/*.json`.

---

## 2. Investigação dos 10 Procedimentos Oficiais

### 2.1. Abrir / Importar Notebook no Molab
- **Via GitHub Mirror:** Acessar a URL no padrão:
  `https://molab.marimo.io/github/<owner>/<repo>/blob/<branch>/<caminho_notebook>.py`
- **Via Upload Manual:** No painel lateral do molab autenticado, importar arquivos `.py` locais para o workspace do usuário.
- **Via URL direta:** Passar uma URL pública de arquivo `.py` para importação.

### 2.2. Instalação de Dependências Python
- **PEP 723 (Inline Script Metadata):** O marimo e o molab suportam metadados inline de script no cabeçalho do arquivo `.py`:
  ```python
  # /// script
  # requires-python = ">=3.12"
  # dependencies = [
  #     "duckdb>=1.2.0",
  #     "pyarrow>=18.0.0",
  #     "marimo-studio[deno]>=0.2.3",
  # ]
  # ///
  ```
- **Painel Package Manager:** No ambiente interativo do molab, o usuário pode adicionar pacotes pela barra lateral ou ao executar células que importam novas bibliotecas.

### 2.3. Inclusão de Arquivos Auxiliares (Multi-file Projects)
- **Comportamento Documentado no molab:**
  > *"Mirror notebooks from GitHub: Currently, this brings just the notebook file down, and does not include your attached storage."*  
  > *(Fonte: https://docs.marimo.io/guides/molab/)*
- **Impacto Crítico:** Ao carregar um notebook via link do GitHub (`molab.marimo.io/github/...`), o molab faz o download **exclusivamente do arquivo `.py` do notebook**. Diretórios locais como `src/` (módulos Python auxiliares), `data/` (arquivos locais) e `__marimo__/` (configurações do studio) **não são clonados automaticamente** pelo container padrão do molab.
- **Armazenamento de Arquivos:** No molab, arquivos extras devem ser enviados manualmente pelo explorador de arquivos lateral do container (`sidebar file tree`) ou montados via storage remoto (S3, Google Drive, Hugging Face).

### 2.4. Disponibilização de Arquivos Parquet
- **Estratégia A (Arquivos Locais no Projeto):** Requer upload manual dos arquivos `.parquet` para o sistema de arquivos efêmero do container molab (`/home/...`), mantendo os caminhos relativos compatíveis com `read_parquet('data/parquet/...')`.
- **Estratégia B (Armazenamento em Nuvem / S3):** O DuckDB no container molab suporta leitura direta via HTTP/S3 (`httpfs` extension):
  ```sql
  SELECT * FROM read_parquet('https://.../data.parquet')
  ```
- **Estratégia C (Parquet Remoto Público / GitHub Raw):** Como o repositório pode disponibilizar os Parquet sintéticos publicamente, o DuckDB pode lê-los via URL raw sem autenticação privada.

### 2.5. Compartilhar Notebook vs. 2.6. Compartilhar como App
- **Modo Notebook (Editor):** Link padrão do molab (`mode=edit`) exibe a árvore de arquivos, células de código, logs e ferramentas de desenvolvimento.
- **Modo App (`mode=read` / Run as App):** O molab permite compartilhar como aplicação através do menu `Share > Run as app`. No modo app, o usuário visualiza apenas a casca da aplicação gerada pelo marimo, sem acesso às células de código.

### 2.7. Execução de Views do marimo-studio
- O `marimo-studio` (lançado em 01/10/2026) opera em nível de projeto:
  ```text
  notebook.py
  __marimo__/studio/<notebook_name>/<view_name>/
      ├── view.toml
      ├── package.json
      ├── src/
      │    ├── App.svelte
      │    └── ...
      └── .artifacts/
  ```
- Quando o comando `marimo run notebook.py` é invocado em um servidor onde o pacote `marimo-studio` está instalado no mesmo ambiente Python, o marimo intercepta a rota raiz e serve a view customizada declarada em `[tool.marimo-studio] default = "dashboard"`.
- **Limitação no molab:** O molab roda uma imagem conteinerizada padrão com o marimo básico (`marimo`). A imagem padrão do molab **não inclui pré-instalado o `marimo-studio[deno]`** nem o binário do **Deno**. Além disso, o espelhamento padrão do GitHub não baixa a pasta `__marimo__/studio/`.

### 2.8. Utilização de Frontend Customizado & 2.9. Dependências Node/Svelte
- Para que o `marimo-studio` funcione em modo dinâmico (desenvolvimento ou compilação on-the-fly), é necessário que o ambiente possua um engine Deno/Node para executar o bundler Vite e o compilador Svelte.
- Em ambientes que não possuem Deno/Node, a compilação só é viável se os artefatos compilados (`.artifacts/`) ou a versão estática pré-exportada forem fornecidos.

### 2.10. Servir Assets Estáticos
- O marimo suporta servir arquivos estáticos a partir de um diretório `public/` vizinho ao notebook.
- No `marimo-studio`, os assets são empacotados pelo Vite e servidos como blueprints iframe ou componentes compilados vinculados ao WebSocket do marimo.

---

## 3. Matriz de Requisitos para Execução no Molab

| Requisito do Projeto | Disponível no molab Padrão? | Desafio Identificado |
|---|---|---|
| **Python 3.12** | Sim (Ambiente Linux Container) | Compatível. |
| **DuckDB** | Sim (Instalável via uv / PEP 723) | Compatível. |
| **Parquet Local (`data/parquet/`)** | Não automático (apenas `.py` é espelhado) | O espelhamento do GitHub não baixa pastas de dados; requer download programático ou Parquet remoto. |
| **Código Modular (`src/analytics/`)** | Não automático | `from src.analytics...` falha se apenas o arquivo do notebook for baixado. |
| **marimo-studio[deno]** | Não pré-instalado | Deve ser declarado em `dependencies` do PEP 723. |
| **Deno Binary** | Não garantido no container base | `marimo-studio[deno]` baixa o binário Deno na instalação do wheel. |
| **Estrutura `__marimo__/studio/`** | Não baixada no espelhamento GitHub | Sem a pasta `__marimo__/studio/`, o servidor cai no fallback do notebook padrão. |

---

## 4. Referências Documentais Oficiais

1. **marimo Guides - Run in the cloud with molab:** `https://docs.marimo.io/guides/molab/`
2. **marimo Publishing Guide:** `https://docs.marimo.io/guides/publishing/`
3. **marimo Studio Skill & Packaging Specs:** `uvx --with marimo-studio agent-plugins read marimo-studio`
4. **marimo Data Apps Guide:** `https://docs.marimo.io/guides/apps/`
5. **marimo GitHub Mirroring Service:** `https://molab.marimo.io/github` e `https://marimo.app/gh/`
6. **marimo Static & WebAssembly Previews:** `https://docs.marimo.io/guides/publishing/playground/`
