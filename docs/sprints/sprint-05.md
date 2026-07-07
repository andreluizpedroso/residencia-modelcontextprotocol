# Sprint 5 — Client MCP Customizado + Conexão com um Host Real

**Data:** 2026-07-07
**Status:** Concluída ✅

---

## Objetivo

Construir um Client MCP próprio (em vez de usar apenas smoke tests ou o Inspector), genérico o suficiente para conversar com qualquer um dos servers já construídos, e documentar como conectar esses mesmos servers a um Host real (Claude Desktop).

---

## O que foi construído

`client.py`: um Client de linha de comando que sobe qualquer server MCP via `stdio` e expõe 4 ações:

| Ação | Uso | Equivalente no protocolo |
|---|---|---|
| `list` | `client.py --server "..." list` | `list_tools` + `list_resources` + `list_resource_templates` + `list_prompts` |
| `call` | `client.py --server "..." call <tool> chave=valor ...` | `call_tool` |
| `read` | `client.py --server "..." read <uri>` | `read_resource` |
| `prompt` | `client.py --server "..." prompt <nome> chave=valor ...` | `get_prompt` |

O `--server` recebe o comando completo para subir **qualquer** server já construído (Sprint 2 ou 3), tornando o Client agnóstico ao server-alvo — o mesmo princípio do MCP Inspector, só que escrito por nós.

Validado contra os dois servers já existentes:

```
uv run client.py --server "uv run --directory ../sprint-02-tools-server server.py" list
uv run client.py --server "uv run --directory ../sprint-02-tools-server server.py" call adicionar_tarefa titulo="..."
uv run client.py --server "uv run --directory ../sprint-03-resources-prompts server.py" read notes://json-rpc
uv run client.py --server "uv run --directory ../sprint-03-resources-prompts server.py" prompt resumir_nota note_id=mcp-intro
```

---

## Bug encontrado e corrigido durante a construção

A primeira versão de `chamar_tool` levantava `raise SystemExit(1)` **dentro** dos blocos `async with stdio_client(...)` / `async with ClientSession(...)`. Isso quebrou o cleanup do `anyio`: em vez de um exit code limpo, o processo terminava com um `BaseExceptionGroup` e um traceback longo, mesmo o erro de negócio (`Tarefa #999 nao encontrada`) já tendo sido corretamente reportado pelo server.

**Causa:** `SystemExit` não é uma `Exception` comum — é levantado dentro do escopo de um `TaskGroup` do `anyio`, que trata qualquer exceção não capturada durante o `__aexit__` dos context managers como parte do cancelamento estruturado, embrulhando tudo em um `ExceptionGroup`.

**Correção:** as funções de ação passaram a **retornar** um `bool`/exit code em vez de levantar `SystemExit`. O `run()` retorna esse código, e só depois que `asyncio.run(...)` já terminou — ou seja, fora de qualquer `async with` — o `main()` levanta `SystemExit(exit_code)`.

Essa é uma lição geral, não específica do MCP: **nunca levante `SystemExit` (nem chame `sys.exit`) de dentro de código assíncrono estruturado (`async with`, `TaskGroup`)** — sempre propague um valor de retorno e só encerre o processo depois que o event loop e os context managers já fecharam.

---

## Conectando a um Host real (Claude Desktop)

Um Host real (como o Claude Desktop) não precisa do nosso `client.py` — ele já tem um Client MCP embutido. Basta declarar o server no arquivo de configuração:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gerenciador-de-tarefas": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "C:\\caminho\\completo\\para\\servers\\sprint-02-tools-server",
        "server.py"
      ]
    }
  }
}
```

Depois de salvar e reiniciar o Claude Desktop, as Tools do server aparecem disponíveis na conversa, e o próprio Claude decide quando chamá-las com base no que você pede.

> Esta etapa não foi validada nesta sprint porque o Claude Desktop não está instalado nesta máquina. É a única parte da Sprint 5 que depende de uma ação manual sua fora deste ambiente — o restante (Client customizado, testes, smoke tests) foi construído e validado normalmente.

---

## Arquitetura

```
                     ┌── client.py (nosso, CLI)  ──┐
Servers MCP  ◄──stdio──┤                            ├──► qualquer um fala com qualquer um
(Sprint 2/3)         └── Claude Desktop (Host real) ─┘
```

O ponto central da sprint: um Server MCP bem construído não sabe (nem precisa saber) qual Client está do outro lado — o mesmo `server.py` da Sprint 2 já foi conectado por 4 Clients diferentes até agora: o smoke test da própria sprint, o MCP Inspector, este `client.py`, e (potencialmente) o Claude Desktop.

---

## Decisões Arquiteturais

| Decisão | Escolha | Alternativa descartada | Motivo |
|---------|---------|------------------------|--------|
| Escopo do Client | Genérico (`--server` configurável), 4 ações | Client fixo, hardcoded para um único server | Reforça que o protocolo é o contrato, não o server específico — mesmo princípio do Inspector |
| Parsing de argumentos de Tool | `json.loads` com fallback para string crua | Sempre string | Permite passar `id=999` (int) ou `apenas_pendentes=true` (bool) sem o usuário se preocupar com tipos, casando com o schema gerado na Sprint 2 |
| Sinalização de erro do processo | Exit code (`0`/`1`) retornado de `run()`, `SystemExit` só em `main()` | `SystemExit` disparado de qualquer lugar | Evitar quebrar o cleanup estruturado do `anyio` — bug real encontrado e corrigido nesta sprint |
| Validação do Host real | Documentar a configuração do Claude Desktop sem poder executá-la | Pular essa parte | Claude Desktop não está instalado neste ambiente; a configuração é registrada para você validar manualmente |

---

## Arquivos Criados

| Arquivo/Pasta | Função |
|---|---|
| `docs/sprints/sprint-05.md` | Este documento |
| `servers/sprint-05-custom-client/client.py` | Client MCP customizado com 4 ações (list/call/read/prompt) |
| `servers/sprint-05-custom-client/tests/test_client.py` | Testes unitários (parsing) + testes de integração reais contra o server da Sprint 2 |

---

## Conceitos Ensinados

- Um Client MCP não precisa ser um Host completo — pode ser um script simples que sobe `stdio_client` + `ClientSession` e chama as operações do protocolo
- O mesmo Server pode ser consumido por múltiplos Clients diferentes (smoke test, Inspector, client customizado, Host real) sem nenhuma mudança no código do Server
- `SystemExit`/`sys.exit()` não deve ser levantado de dentro de blocos `async with` de bibliotecas com concorrência estruturada (`anyio`/`TaskGroup`) — propague um valor de retorno em vez disso
- Um Host real (Claude Desktop) descobre servers via um arquivo de configuração JSON (`mcpServers`), apontando para o comando que sobe o server — não requer nenhum código de integração

---

## Perguntas de Validação

1. Por que o `client.py` recebe o comando do server via `--server` em vez de ter o comando fixo no código?

   Para ser genérico e reutilizável contra qualquer server MCP que fale `stdio`, não só um específico — o mesmo princípio de design usado pelo próprio MCP Inspector.

2. O que deu errado na primeira versão de `chamar_tool`, e por que envolvia especificamente `SystemExit` e não uma exceção comum?

   Ela levantava `SystemExit(1)` dentro dos blocos `async with stdio_client(...)`/`async with ClientSession(...)`. Como `SystemExit` não é tratado como uma exceção de aplicação comum pelo `anyio`, ele interrompe o cleanup estruturado do `TaskGroup` e gera um `BaseExceptionGroup` com traceback longo, em vez de um encerramento limpo.

3. Por que o mesmo `server.py` da Sprint 2 pôde ser usado, sem nenhuma alteração, pelo smoke test, pelo Inspector e por este Client customizado?

   Porque o Server não sabe (nem precisa saber) quem está do outro lado — ele só implementa o protocolo MCP sobre `stdio`. Qualquer Client que fale o mesmo protocolo consegue se conectar, sem nenhuma mudança no Server.

4. O que precisa existir no `claude_desktop_config.json` para o Claude Desktop reconhecer um novo server MCP?

   Uma entrada em `mcpServers` com um nome para o server e um `command`/`args` que sobe o processo do server (ex: `uv run --directory <caminho> server.py`).

5. Por que faz sentido usar `json.loads` para interpretar os argumentos passados na linha de comando (`id=999`) em vez de sempre tratá-los como string?

   Porque as Tools esperam tipos específicos (int, bool) conforme o schema gerado na Sprint 2 — `json.loads` converte `"999"` em `int 999` e `"true"` em `bool True` automaticamente, evitando que o usuário precise se preocupar manualmente com conversão de tipos.

---

## Code Review

**Nota: 8.5/10**

**Pontos positivos:**
- Cliente genérico (não hardcoded para um server específico), reforçando a natureza do protocolo
- Bug real de interação entre `SystemExit` e `anyio.TaskGroup` foi identificado e corrigido durante a própria sprint, não só documentado depois
- Testes de integração rodam contra um server real via subprocess, não apenas mocks — pegaria regressões de protocolo de verdade
- `parse_value` com fallback seguro (JSON válido → tipo nativo; inválido → string) evita quebrar em argumentos com texto livre

**Pontos de atenção:**
- `parse_kv_pairs` usa `pair.split("=", 1)` sem tratar ausência de `=` — um argumento mal formatado gera `ValueError` genérico do Python em vez de uma mensagem clara; aceitável para um exercício de CLI interno, mas seria o primeiro ajuste de UX antes de qualquer uso por terceiros
- Testes de integração dependem de um caminho relativo (`../sprint-02-tools-server`) e do `uv` disponível no `PATH` — funciona bem localmente, mas quebraria em CI sem ajuste de working directory

---

## Perguntas de Entrevista

1. Por que `sys.exit()`/`SystemExit` dentro de um `async with TaskGroup` é perigoso, de forma geral — não só neste exercício?

   Porque bibliotecas de concorrência estruturada tratam o cancelamento e o encerramento de tarefas de forma coordenada; uma `SystemExit` levantada no meio desse escopo interrompe esse fluxo de forma inesperada, sendo capturada e reembalada em um `ExceptionGroup`, mascarando a intenção original ("só quero encerrar o processo com este código") com um erro aparentemente não relacionado.

2. Se você precisasse que este Client customizado funcionasse tanto com servers locais (`stdio`) quanto remotos (HTTP), o que mudaria na assinatura de `run()`?

   Adicionaria um parâmetro para escolher o transporte (ex: `transporte: Literal["stdio", "http"]` e uma URL quando HTTP), e trocaria `stdio_client(params)` por `streamable_http_client(url, ...)` condicionalmente, mantendo o resto da lógica (ações list/call/read/prompt) igual, já que ela opera sobre a `ClientSession`, não sobre o transporte.

3. Do ponto de vista de um Host como o Claude Desktop, o que ele precisa fazer, na prática, quando o usuário faz uma pergunta que pode ser respondida por uma Tool exposta por um dos servers configurados?

   O Host inclui a lista de Tools disponíveis (obtida via `list_tools` de cada Client conectado) no contexto enviado ao LLM. O modelo decide, com base na pergunta, se deve chamar alguma Tool; se decidir, o Host recebe essa decisão e invoca `call_tool` no Client correspondente, devolvendo o resultado ao modelo para compor a resposta final.

**Nota geral: 9/10**

**Q1 (9/10):** Explicação correta e bem articulada sobre por que `SystemExit` conflita com concorrência estruturada.

**Q2 (9/10):** Resposta sólida, identifica corretamente que só o transporte muda, não a lógica das ações — mostra entendimento da separação de camadas.

**Q3 (9/10):** Descreve corretamente o ciclo "Host expõe tools ao modelo → modelo decide → Host executa via Client". Poderia acrescentar que o resultado da Tool volta para o modelo como mais uma mensagem de contexto antes da resposta final ao usuário.
