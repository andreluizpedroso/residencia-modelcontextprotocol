# Sprint 4 — Testando com MCP Inspector

**Data:** 2026-07-07
**Status:** Concluída ✅

---

## Objetivo

Aprender a usar o **MCP Inspector**, a ferramenta oficial de debug/inspeção do MCP, para explorar um Server já construído (Sprints 2 e 3) sem precisar escrever um Client próprio — tanto no modo visual (browser) quanto no modo `--cli` (linha de comando, sem browser).

Diferente das sprints anteriores, aqui não construímos um Server novo: usamos o Inspector para inspecionar os servers que já existem (`sprint-02-tools-server`, `sprint-03-resources-prompts`).

---

## O que é o MCP Inspector

O Inspector é uma ferramenta Node distribuída via `npx`, mantida em [github.com/modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector). Ele sobe **dois processos**:

- Um **proxy server** (porta `6277` por padrão) que fala o protocolo MCP com o Server-alvo (por `stdio`, no nosso caso)
- Uma **UI web** (porta `6274` por padrão) que consome o proxy e mostra tools, resources e prompts de forma navegável, junto com o payload JSON-RPC bruto de cada requisição/resposta

Comando geral: `npx @modelcontextprotocol/inspector <comando-para-rodar-o-server> [args...]`.

---

## Validação feita nesta sprint

**1. Modo visual**, contra o server da Sprint 2:

```
cd servers/sprint-02-tools-server
npx @modelcontextprotocol/inspector uv run server.py
```

Log de inicialização confirmado:

```
⚙️ Proxy server listening on localhost:6277
🔑 Session token: <token>
🚀 MCP Inspector is up and running at:
   http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=<token>
```

A UI abre no browser autenticada via token na própria URL (evita expor o proxy sem autenticação na rede local).

**2. Modo `--cli`**, sem abrir browser — útil para checagens rápidas ou scripts:

Listar as tools expostas e seu JSON Schema completo (gerado automaticamente pelo `FastMCP` a partir dos type hints, exatamente como discutido na Sprint 2):

```
npx @modelcontextprotocol/inspector --cli uv run server.py --method tools/list
```

Chamar uma tool diretamente, passando argumentos:

```
npx @modelcontextprotocol/inspector --cli uv run server.py \
  --method tools/call --tool-name adicionar_tarefa --tool-arg titulo="Testar via Inspector CLI"
```

Retornou:

```json
{
  "content": [{ "type": "text", "text": "Tarefa #1 criada: 'Testar via Inspector CLI'" }],
  "structuredContent": { "result": "Tarefa #1 criada: 'Testar via Inspector CLI'" },
  "isError": false
}
```

Confirma exatamente o mesmo formato de resposta (`content` + `structuredContent` + `isError`) que validamos "na mão" com `ClientSession` nas Sprints 2 e 3 — o Inspector não é mágica, ele fala o mesmo protocolo que qualquer Client.

---

## Arquitetura

```
npx @modelcontextprotocol/inspector uv run server.py
        │
        ├─ spawna o server como subprocesso, falando stdio (igual ao nosso smoke test)
        ├─ Proxy Server :6277  ── traduz entre a UI web e o processo do Server
        └─ UI Web :6274        ── lista tools/resources/prompts, permite chamar cada um
                                   e inspecionar o JSON-RPC bruto de cada troca
```

O Inspector não substitui os smoke tests com `ClientSession` que já escrevemos — ele serve para **exploração manual e interativa**, especialmente útil quando ainda não se sabe exatamente o que testar, ou para depurar visualmente o schema/payload de uma Tool nova.

---

## Decisões Arquiteturais

| Decisão | Escolha | Alternativa descartada | Motivo |
|---------|---------|------------------------|--------|
| Servers usados como alvo | `sprint-02-tools-server` e `sprint-03-resources-prompts` já existentes | Criar um server novo só para esta sprint | O objetivo é aprender a *ferramenta de inspeção*, não repetir a construção de Tools/Resources |
| Modo de uso documentado | Visual (browser) **e** `--cli` | Só o modo visual | O modo `--cli` é o que permite automatizar checagens do Inspector em scripts/CI — vale registrar os dois |
| Limpeza de processos | Encerrar explicitamente o proxy/UI (`TaskStop`/`Stop-Process`) após validar | Deixar rodando em background | O Inspector sobe dois processos de rede (portas 6274/6277); like qualquer processo de servidor, não deve ficar órfão consumindo porta depois do teste |

---

## Arquivos Criados

| Arquivo/Pasta | Função |
|---|---|
| `docs/sprints/sprint-04.md` | Este documento — não há código novo, o "exercício" é o uso do Inspector contra servers já existentes |

---

## Conceitos Ensinados

- O MCP Inspector é composto por um proxy server (fala MCP com o alvo) e uma UI web (consome o proxy)
- `npx @modelcontextprotocol/inspector <comando>` sobe os dois processos apontando para qualquer server MCP executável
- O modo `--cli` permite listar tools/resources/prompts e chamá-los sem abrir browser — útil para automação e para quem está numa sessão sem interface gráfica
- O JSON Schema de cada Tool exibido pelo Inspector é gerado automaticamente a partir dos type hints e docstrings — o mesmo mecanismo estudado na Sprint 2, só que visualizado de fora
- O formato de resposta (`content`, `structuredContent`, `isError`) é o mesmo tanto via Inspector quanto via `ClientSession` direto — reforça que o Inspector é só mais um Client MCP, não um mecanismo especial

---

## Perguntas de Validação

> *(A preencher com as respostas do usuário)*

1. Quais são os dois processos que o MCP Inspector sobe, e qual a função de cada um?
2. Qual a vantagem prática do modo `--cli` sobre o modo visual, e em que situação você escolheria cada um?
3. Por que o JSON Schema que o Inspector mostra para uma Tool é idêntico ao que já teríamos previsto lendo o código da Sprint 2 (type hints + docstring)?
4. O Inspector usa um token de sessão na própria URL. Que problema de segurança isso evita?
5. Depois de rodar o Inspector, por que é importante encerrar os processos do proxy/UI explicitamente, em vez de simplesmente fechar a aba do browser?

---

## Code Review

Não aplicável nesta sprint — não há código de aplicação novo, apenas o uso de uma ferramenta externa (Inspector) contra os servers das Sprints 2 e 3, cujo code review já foi feito em seus respectivos documentos.

---

## Perguntas de Entrevista

> *(A preencher com as respostas do usuário)*

1. Como o MCP Inspector ajudaria você a depurar um bug relatado por um usuário de produção num server MCP, mesmo sem acesso ao código-fonte do server?
2. Por que faz sentido o Inspector existir como uma ferramenta separada do SDK, em vez de vir embutido em cada Client/Host?
3. Em que ponto do ciclo de desenvolvimento de um Server MCP (antes do primeiro Tool? depois de vários Tools? antes de subir pra produção?) o Inspector agrega mais valor, na sua opinião?
