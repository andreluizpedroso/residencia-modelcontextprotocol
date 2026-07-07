# Sprint 2 — Primeiro MCP Server com Tools

**Data:** 2026-07-07
**Status:** Concluída ✅

---

## Objetivo

Construir o primeiro MCP Server de verdade, expondo Tools reais através do SDK oficial, e validar o funcionamento fim a fim com um Client MCP real (não só testar funções Python isoladas).

---

## O que foi construído

Um server chamado `gerenciador-de-tarefas` (`server.py`), com estado em memória e 4 Tools:

| Tool | Assinatura | O que faz |
|---|---|---|
| `adicionar_tarefa` | `(titulo: str) -> str` | Cria uma tarefa nova, retorna confirmação com o ID gerado |
| `listar_tarefas` | `(apenas_pendentes: bool = False) -> list[dict]` | Lista as tarefas, com filtro opcional |
| `concluir_tarefa` | `(id: int) -> str` | Marca uma tarefa como concluída; levanta erro se o ID não existe |
| `remover_tarefa` | `(id: int) -> str` | Remove uma tarefa; levanta erro se o ID não existe |

---

## Arquitetura

O server usa a API de alto nível do SDK, `FastMCP`: cada função Python decorada com `@mcp.tool()` vira uma Tool MCP automaticamente — o SDK deriva o JSON Schema dos parâmetros a partir dos **type hints**, e a descrição da Tool a partir da **docstring**. Isso elimina o boilerplate de registrar manualmente o schema e o dispatcher de cada Tool.

```
Client MCP (ClientSession) ──stdio──> server.py (FastMCP)
                                          ├─ adicionar_tarefa
                                          ├─ listar_tarefas
                                          ├─ concluir_tarefa
                                          └─ remover_tarefa
```

Validamos isso de duas formas complementares:

1. **Testes unitários** (`tests/test_tools.py`, pytest) — chamam as funções Python diretamente, sem passar pelo protocolo MCP. Rápido, cobre a lógica de negócio (IDs sequenciais, filtro de pendentes, erros).
2. **Smoke test com Client real** — um script que sobe o server como subprocesso via `stdio_client` + `ClientSession`, chama `list_tools()` e `call_tool(...)` de verdade. Isso comprovou que o schema é gerado corretamente, que o dispatch funciona, e que uma exceção dentro de uma Tool vira `isError=True` na resposta ao Client — sem derrubar o processo do server.

---

## Decisões Arquiteturais

| Decisão | Escolha | Alternativa descartada | Motivo |
|---------|---------|------------------------|--------|
| API do SDK | `FastMCP` (alto nível) | `mcp.server.Server` (baixo nível) | Decorators inferem schema a partir de type hints/docstring; menos boilerplate para o primeiro server de verdade |
| Domínio do exercício | Gerenciador de tarefas em memória | Wrapper de API externa (ex: clima) | Sem dependência de rede/chave de API — foco 100% em entender Tools, não em lidar com integrações externas |
| Armazenamento | `dict` em memória, processo único | Arquivo ou banco de dados | Estado só precisa sobreviver durante a sessão `stdio`; persistência real está fora do escopo desta sprint |
| Sinalização de erro | `raise ValueError(...)` dentro da Tool | Retornar uma string de erro manualmente | `FastMCP` converte a exceção automaticamente em `isError=True` no resultado — comprovado no smoke test |
| Estratégia de teste | pytest nas funções + smoke test com `ClientSession` real | Só uma das duas abordagens | pytest cobre a lógica rápido; o smoke test garante que o *protocolo* MCP (schema, dispatch, serialização) também funciona, não só o Python puro |

---

## Arquivos Criados

| Arquivo/Pasta | Função |
|---|---|
| `docs/sprints/sprint-02.md` | Este documento |
| `servers/sprint-02-tools-server/server.py` | O MCP Server com as 4 Tools |
| `servers/sprint-02-tools-server/tests/test_tools.py` | Testes unitários das Tools (pytest) |
| `servers/sprint-02-tools-server/pyproject.toml` | Dependências (`mcp`, `pytest` como dev) + config do pytest (`pythonpath`) |

---

## Conceitos Ensinados

- `FastMCP`: API de alto nível do SDK oficial que gera o server a partir de funções Python decoradas
- Como type hints + docstring viram o JSON Schema e a descrição de uma Tool, automaticamente
- Diferença entre testar a função Python pura (unit test) e validar o protocolo MCP de ponta a ponta (client real conectando via `stdio`)
- Como uma exceção dentro de uma Tool vira `isError=True` para o Client, sem derrubar o processo do Server
- `mcp.run()` inicia o loop do server, usando `stdio` como transporte por padrão

---

## Perguntas de Validação

> *(A preencher com as respostas do usuário)*

1. O que o decorator `@mcp.tool()` faz automaticamente a partir da assinatura da função (nomes, tipos, docstring)?
2. Por que faz sentido ter tanto testes unitários da função Python quanto um smoke test via `ClientSession` real? O que cada um garante que o outro não garante?
3. O que acontece, do ponto de vista do Client, quando uma Tool levanta uma exceção? O processo do Server cai?
4. Por que o estado (`_tasks`) foi guardado em um dict em memória em vez de um arquivo ou banco? Que limitação prática isso traz?
5. Qual a diferença entre a API `FastMCP` (alto nível) e a API `Server` de baixo nível do SDK? Por que começamos pela primeira?

---

## Code Review

**Nota: 8/10**

**Pontos positivos:**
- Uso correto de `raise ValueError` para erros de negócio, deixando o SDK converter para o formato de erro do protocolo — nenhum tratamento manual de erro necessário
- Separação clara entre lógica (funções decoradas, testáveis diretamente) e o `main()`/`mcp.run()` que só sobe o transporte
- Testes cobrem tanto o caminho feliz quanto os dois casos de erro (`concluir`/`remover` com ID inexistente)
- Validado fim a fim com um Client MCP real, não só com chamadas de função Python — pegaria erros de schema que os testes unitários não pegariam

**Pontos de atenção:**
- `global _next_id` funciona porque `stdio` atende uma única conexão por processo; isso **não seria seguro** se o mesmo server fosse exposto via HTTP a múltiplos clientes simultâneos (condição de corrida no incremento) — ponto que devemos revisitar na Sprint 7
- Nenhuma validação de entrada (ex: `titulo` vazio) — aceitável para o exercício, mas seria o primeiro ajuste antes de qualquer uso real

---

## Perguntas de Entrevista

> *(A preencher com as respostas do usuário)*

1. Como você garantiria que múltiplas chamadas concorrentes a esse server não corrompam o estado, se o transporte fosse HTTP com vários clientes simultâneos?
2. Que tipo de validação de entrada você adicionaria antes de colocar esse server em produção, e por quê?
3. Qual a diferença entre uma Tool que retorna `str` e uma que retorna `list[dict]`? Como isso afeta o schema de saída relatado pelo MCP?
