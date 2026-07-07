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

1. O que o decorator `@mcp.tool()` faz automaticamente a partir da assinatura da função (nomes, tipos, docstring)?

   Ele registra a função como uma Tool MCP, usando o nome da função como nome da Tool, gerando o JSON Schema dos parâmetros a partir dos type hints, e usando a docstring como descrição exibida ao Client. Tudo isso sem precisar declarar o schema manualmente.

2. Por que faz sentido ter tanto testes unitários da função Python quanto um smoke test via `ClientSession` real? O que cada um garante que o outro não garante?

   O teste unitário valida a lógica de negócio rápido (IDs sequenciais, filtros, erros), mas não passa pelo protocolo MCP de verdade. O smoke test com `ClientSession` garante que o schema gerado, a serialização e o dispatch funcionam de ponta a ponta — pegaria, por exemplo, um erro de schema que nenhum teste unitário detectaria.

3. O que acontece, do ponto de vista do Client, quando uma Tool levanta uma exceção? O processo do Server cai?

   O Client recebe um resultado com `isError=True` e a mensagem da exceção no conteúdo. O processo do Server continua rodando normalmente — a exceção é capturada pelo SDK e convertida em erro do protocolo, não propaga para derrubar o servidor.

4. Por que o estado (`_tasks`) foi guardado em um dict em memória em vez de um arquivo ou banco? Que limitação prática isso traz?

   Porque o estado só precisa sobreviver durante a sessão `stdio` daquele processo, e um dict é a forma mais simples de representar isso no exercício. A limitação é que qualquer reinício do processo do Server perde todas as tarefas — não há persistência entre sessões.

5. Qual a diferença entre a API `FastMCP` (alto nível) e a API `Server` de baixo nível do SDK? Por que começamos pela primeira?

   `FastMCP` gera o schema e o dispatch automaticamente a partir de funções decoradas; a API `Server` de baixo nível exige registrar manualmente os handlers e schemas de cada Tool/Resource/Prompt. Começamos pela `FastMCP` porque o objetivo inicial é entender as primitivas do protocolo, não a mecânica interna de registro de handlers.

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

1. Como você garantiria que múltiplas chamadas concorrentes a esse server não corrompam o estado, se o transporte fosse HTTP com vários clientes simultâneos?

   Usaria um lock (`asyncio.Lock`) em torno das operações que leem e incrementam `_next_id`/`_tasks`, ou moveria o estado para um armazenamento que já trata concorrência corretamente (ex: um banco de dados com transações), em vez de um dict em memória compartilhado sem sincronização.

2. Que tipo de validação de entrada você adicionaria antes de colocar esse server em produção, e por quê?

   Validaria que `titulo` não é vazio/só espaços em branco, e limitaria seu tamanho máximo, para evitar tarefas inúteis ou payloads anormalmente grandes. Também validaria que `id` em `concluir_tarefa`/`remover_tarefa` é um inteiro positivo antes mesmo de consultar o dict.

3. Qual a diferença entre uma Tool que retorna `str` e uma que retorna `list[dict]`? Como isso afeta o schema de saída relatado pelo MCP?

   Uma Tool que retorna `str` gera um `outputSchema` simples (`{"result": {"type": "string"}}`), enquanto uma que retorna `list[dict]` gera um schema de array de objetos. Isso importa porque o Client (ou o LLM do lado do Host) usa esse schema para saber como interpretar e, eventualmente, validar a resposta antes de usá-la.

**Nota geral: 9/10**

**Q1 (9/10):** Resposta tecnicamente correta — lock ou storage transacional são as duas soluções padrão. Gap menor: poderia mencionar que, em muitos casos reais, é mais simples desenhar o storage para já ser "concurrency-safe" (ex: um banco) do que gerenciar locks manualmente na camada da aplicação.

**Q2 (9/10):** Validações pertinentes e no nível certo de detalhe para este exercício.

**Q3 (9/10):** Resposta correta e direta, identifica o mecanismo (outputSchema) e a consequência prática (Client sabe como interpretar o retorno).
