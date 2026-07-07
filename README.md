# Estudo-MCP — Model Context Protocol na Prática

![Sprint](https://img.shields.io/badge/Sprints-8%2F8-success)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![MCP SDK](https://img.shields.io/badge/MCP-python--sdk-000000)
![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9?logo=uv&logoColor=white)
![Pytest](https://img.shields.io/badge/pytest-tested-0A9EDC?logo=pytest&logoColor=white)

Estudo guiado e prático do **Model Context Protocol (MCP)**, construído do zero em 8 sprints incrementais. Cada sprint entrega um MCP Server funcional e testado — não apenas exemplos de documentação — cobrindo o protocolo inteiro: Tools, Resources, Prompts, Sampling, Roots, transporte remoto e autenticação.

---

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [Progresso das sprints](#progresso-das-sprints)
- [O que foi construído](#o-que-foi-construído)
- [Bugs reais encontrados pelo caminho](#bugs-reais-encontrados-pelo-caminho)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como rodar](#como-rodar)
- [Metodologia](#metodologia)
- [Referências](#referências)

---

## Sobre o projeto

O [Model Context Protocol](https://github.com/modelcontextprotocol) é o padrão aberto que permite que aplicações de IA (Hosts) se conectem, de forma uniforme, a ferramentas e fontes de dados externas (Servers) — eliminando a necessidade de uma integração proprietária para cada combinação de aplicação × ferramenta.

Este repositório documenta um estudo do zero do MCP, indo além da leitura da especificação: cada sprint produz um **server MCP real, com testes automatizados e validação de ponta a ponta** (via `ClientSession` real, MCP Inspector, ou ambos), cobrindo progressivamente:

`Tools` → `Resources & Prompts` → `Inspeção/debug` → `Client customizado` → `Sampling & Roots` → `Transporte HTTP + Auth` → `Projeto final`

---

## Progresso das Sprints

| # | Sprint | Entregável | Status |
|---|--------|------------|:---:|
| 1 | [Fundamentos do MCP + setup do ambiente](docs/sprints/sprint-01.md) | Ambiente `uv` + SDK oficial validado | ✅ |
| 2 | [Primeiro MCP Server — Tools](docs/sprints/sprint-02.md) | Gerenciador de tarefas ([`servers/sprint-02-tools-server`](servers/sprint-02-tools-server)) | ✅ |
| 3 | [Resources & Prompts](docs/sprints/sprint-03.md) | Biblioteca de notas ([`servers/sprint-03-resources-prompts`](servers/sprint-03-resources-prompts)) | ✅ |
| 4 | [Testando com MCP Inspector](docs/sprints/sprint-04.md) | Validação visual e via `--cli` | ✅ |
| 5 | [Client MCP customizado + Host real](docs/sprints/sprint-05.md) | Client genérico ([`servers/sprint-05-custom-client`](servers/sprint-05-custom-client)) | ✅ |
| 6 | [Sampling & Roots](docs/sprints/sprint-06.md) | Server com as duas primitivas ([`servers/sprint-06-sampling-roots`](servers/sprint-06-sampling-roots)) | ✅ |
| 7 | [Transporte HTTP + Autenticação](docs/sprints/sprint-07.md) | Server `streamable-http` com Bearer token ([`servers/sprint-07-http-auth`](servers/sprint-07-http-auth)) | ✅ |
| 8 | [Projeto final](docs/sprints/sprint-08.md) | Assistente de repositório Git ([`servers/sprint-08-final-project`](servers/sprint-08-final-project)) | ✅ |

Cada sprint em `docs/sprints/` segue um formato fixo: **objetivo, conceitos ensinados, decisões arquiteturais, perguntas de validação, code review (com nota) e perguntas de entrevista** — ver [Metodologia](#metodologia).

---

## O que foi construído

| Server | Primitivas MCP | Ponto forte |
|---|---|---|
| `sprint-02-tools-server` | Tools | 4 Tools com estado em memória, testes unitários + smoke test via Client real |
| `sprint-03-resources-prompts` | Resources (estática + template) e Prompts | Duas formas de retorno de Prompt (`str` e `list[Message]`) |
| `sprint-05-custom-client` | Client genérico | Funciona contra qualquer server `stdio`; 4 ações (list/call/read/prompt) |
| `sprint-06-sampling-roots` | Sampling e Roots | Round-trip Server → Client → Server validado com callbacks stub |
| `sprint-07-http-auth` | Transporte HTTP + Auth | `TokenVerifier` customizado, testado com token ausente/inválido/válido |
| `sprint-08-final-project` | Tools + Resources + Prompts | Assistente de repositório Git, testado contra o histórico real deste repo |

Todos os servers são construídos com o [SDK oficial em Python](https://github.com/modelcontextprotocol/python-sdk) (`FastMCP`) e têm suíte de testes própria (`uv run pytest`).

---

## Bugs Reais Encontrados pelo Caminho

Construir os exercícios contra Clients reais (não só ler a documentação) expôs problemas concretos, corrigidos durante o próprio desenvolvimento:

| Sprint | Bug | Causa | Correção |
|---|---|---|---|
| [5](docs/sprints/sprint-05.md) | Traceback ao propagar erro de Tool | `SystemExit` levantado dentro de `async with` quebra o cleanup do `anyio.TaskGroup` | Retornar exit code e só chamar `SystemExit` fora do escopo assíncrono |
| [7](docs/sprints/sprint-07.md) | `DeprecationWarning` silencioso | API de client HTTP trocada (`streamablehttp_client` → `streamable_http_client`) | Migração para a API atual, com `httpx.AsyncClient` explícito |
| [7](docs/sprints/sprint-07.md) | Processo órfão segurando a porta | `uv run` no Windows spawna um processo filho que sobrevive a `Popen.terminate()` | `taskkill /PID <pid> /T /F` (mata a árvore de processos) |
| [8](docs/sprints/sprint-08.md) | `git log`/`git show` travando indefinidamente | Subprocesso do `git` herdava o `stdin` do server, que em `stdio` é o pipe do protocolo MCP | `stdin=subprocess.DEVNULL` explícito em todo `subprocess.run` |
| [8](docs/sprints/sprint-08.md) | Resource template não casava com caminhos aninhados | O SDK gera `[^/]+` para cada `{param}` — não aceita `/` | Barras codificadas como `%2F` no URI, decodificadas no Server |

---

## Estrutura do Repositório

```
MCP/
├── README.md
├── docs/
│   └── sprints/                        # 1 documento por sprint
│       ├── sprint-01.md … sprint-08.md
└── servers/                             # 1 projeto uv independente por sprint
    ├── sprint-01-hello-mcp/
    ├── sprint-02-tools-server/
    ├── sprint-03-resources-prompts/
    ├── sprint-05-custom-client/
    ├── sprint-06-sampling-roots/
    ├── sprint-07-http-auth/
    └── sprint-08-final-project/
```

Cada pasta em `servers/` é um projeto [`uv`](https://docs.astral.sh/uv/) autocontido, com seu próprio `pyproject.toml`, `uv.lock` e ambiente virtual — sem dependências compartilhadas entre sprints.

---

## Como Rodar

Pré-requisitos: [`uv`](https://docs.astral.sh/uv/) instalado (resolve a versão do Python automaticamente).

```bash
# Entrar no projeto de uma sprint especifica
cd servers/sprint-02-tools-server

# Instalar dependencias
uv sync

# Rodar os testes
uv run pytest -v

# Subir o server (transporte stdio, ou streamable-http na Sprint 7)
uv run server.py
```

Para explorar um server interativamente sem escrever código de Client, use o [MCP Inspector](https://github.com/modelcontextprotocol/inspector) (ver Sprint 4):

```bash
npx @modelcontextprotocol/inspector uv run server.py
```

---

## Metodologia

Cada sprint em `docs/sprints/` segue a mesma estrutura:

1. **Objetivo** — o que a sprint entrega
2. **Conceitos ensinados** — o que precisa ser entendido antes do exercício
3. **Decisões arquiteturais** — escolhas de design, com alternativas descartadas e motivo
4. **Perguntas de validação** — verificam entendimento conceitual, respondidas com as próprias palavras
5. **Code review** — nota e feedback concreto sobre o código produzido na sprint
6. **Perguntas de entrevista** — perguntas no estilo de entrevista técnica, com nota e gaps apontados

---

## Referências

- [Model Context Protocol — especificação e SDKs oficiais](https://github.com/modelcontextprotocol)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [uv — gerenciador de projetos Python](https://docs.astral.sh/uv/)
