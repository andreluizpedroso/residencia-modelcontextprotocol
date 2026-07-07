# Sprint 6 — Sampling & Roots

**Data:** 2026-07-07
**Status:** Concluída ✅

---

## Objetivo

Entender duas primitivas menos óbvias do MCP — **Sampling** (o Server pede ao Client para rodar uma inferência de LLM) e **Roots** (o Client informa ao Server quais diretórios/URIs são relevantes) — e validar as duas de ponta a ponta.

Essas duas primitivas invertem o fluxo que vínhamos assumindo até aqui: nas Sprints 2-5, o Client sempre pergunta e o Server sempre responde. Com Sampling e Roots, é o **Server que pergunta algo ao Client** durante a execução de uma Tool.

---

## O que foi construído

Um server chamado `sampling-e-roots` (`server.py`) com 2 Tools:

| Tool | O que faz | Primitiva |
|---|---|---|
| `resumir_via_sampling(texto)` | Pede ao Client, via `ctx.session.create_message(...)`, para gerar um resumo de uma frase | Sampling |
| `listar_roots_do_client()` | Pergunta ao Client, via `ctx.session.list_roots()`, quais Roots ele expõe | Roots |

Ambas recebem um parâmetro `ctx: Context` injetado automaticamente pelo `FastMCP` — é através dele que a Tool acessa a sessão ativa para "falar de volta" com o Client.

---

## Arquitetura

```
Client                                    Server (Tool em execução)
  │                                              │
  │  call_tool("resumir_via_sampling", ...)  ──► │
  │                                              │  ctx.session.create_message(...)
  │  ◄── sampling_callback(messages, ...)  ───────┤  (Server PERGUNTA ao Client)
  │      (Client roda o LLM e responde)          │
  │  ── CreateMessageResult ────────────────────► │
  │                                              │  Tool usa a resposta e retorna
  │  ◄── resultado final da Tool ─────────────────┤
```

O mesmo padrão vale para Roots: `ctx.session.list_roots()` dispara `list_roots_callback` no Client, que responde com a lista de Roots configurada.

Sem um Client que implemente esses dois callbacks, as Tools desta sprint **não funcionam** — é o Client que precisa declarar suporte a Sampling/Roots e responder às perguntas do Server.

---

## Validação

Como nem sempre há um LLM real disponível para testar Sampling isoladamente, a prática comum (usada aqui) é implementar um **callback stub**: uma função Python simples que simula a resposta do Client, só para provar que o *round-trip* Server → Client → Server funciona no nível do protocolo.

```python
async def sampling_stub(context, params):
    ultima_mensagem = params.messages[-1].content.text
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(type="text", text=f"[resumo simulado] {ultima_mensagem[:60]}"),
        model="stub-model",
    )

async def roots_stub(context):
    return types.ListRootsResult(
        roots=[types.Root(uri="file:///C:/projeto-exemplo/", name="projeto-exemplo")]
    )
```

Esses callbacks são passados na construção do `ClientSession(read, write, sampling_callback=..., list_roots_callback=...)`. Os 3 testes (`tests/test_sampling_roots.py`) confirmam:

1. As Tools aparecem no `list_tools()` **sem** o parâmetro `ctx` no schema — `FastMCP` reconhece o tipo `Context` e o exclui automaticamente do JSON Schema exposto ao Client (confirmado também via `npx @modelcontextprotocol/inspector --cli ... --method tools/list`)
2. `resumir_via_sampling` retorna a resposta simulada do stub, provando que o `create_message` chegou até o Client e voltou
3. `listar_roots_do_client` retorna o Root configurado no stub, provando o mesmo para `list_roots`

---

## Decisões Arquiteturais

| Decisão | Escolha | Alternativa descartada | Motivo |
|---------|---------|------------------------|--------|
| Validação de Sampling | Callback stub determinístico | Configurar uma API key de LLM real | Foco no *mecanismo do protocolo* (o round-trip Server↔Client), não em testar um provedor de LLM específico; também evita depender de credenciais externas no exercício |
| Acesso à sessão dentro da Tool | Parâmetro `ctx: Context` injetado pelo `FastMCP` | Uma variável global apontando para a sessão ativa | `Context` já é o mecanismo oficial do SDK para isso, e o SDK cuida de excluí-lo do schema automaticamente |
| Exercício de Roots | Só listar os Roots recebidos, sem tocar no filesystem | Contar/ler arquivos de verdade em cada Root | URIs `file://` têm particularidades de parsing por sistema operacional (especialmente Windows); o conceito central — o Client informa o Server sobre o escopo relevante — não depende de manipular arquivos de verdade |

---

## Arquivos Criados

| Arquivo/Pasta | Função |
|---|---|
| `docs/sprints/sprint-06.md` | Este documento |
| `servers/sprint-06-sampling-roots/server.py` | Server com as Tools de Sampling e Roots |
| `servers/sprint-06-sampling-roots/tests/test_sampling_roots.py` | Testes com callbacks stub, validando o round-trip completo |

---

## Conceitos Ensinados

- Sampling inverte o fluxo usual: é o **Server** que pede ao **Client** para rodar uma inferência de LLM, via `ctx.session.create_message(...)`
- Roots é o mecanismo pelo qual o **Client** informa ao Server quais diretórios/URIs são relevantes para a tarefa, via `ctx.session.list_roots()`
- O parâmetro `ctx: Context`, injetado automaticamente pelo `FastMCP`, dá à Tool acesso à sessão ativa — e é excluído do JSON Schema exposto ao Client
- Sem um Client que implemente `sampling_callback`/`list_roots_callback`, essas Tools não têm como funcionar — a primitiva depende de suporte dos dois lados
- Testar Sampling sem um LLM real é possível e útil: um callback stub determinístico valida o protocolo sem precisar de credenciais externas

---

## Perguntas de Validação

1. Por que Sampling é descrito como uma "inversão de fluxo" em relação a Tools e Resources?

   Porque em Tools e Resources é sempre o Client que inicia a interação (chama uma Tool, lê uma Resource) e o Server responde. Em Sampling, é o Server, no meio da execução de uma Tool, que envia uma requisição para o Client (`create_message`) e espera uma resposta — os papéis de quem pergunta e quem responde se invertem.

2. O que aconteceria se chamássemos `resumir_via_sampling` a partir de um Client que não implementou `sampling_callback`?

   A chamada falharia — o Client não teria como responder à requisição `create_message` vinda do Server, então a Tool receberia um erro em vez do resultado esperado.

3. Por que o parâmetro `ctx: Context` não aparece no JSON Schema da Tool, mesmo fazendo parte da assinatura da função Python?

   Porque o `FastMCP` reconhece o tipo `Context` especificamente e o trata como um parâmetro de infraestrutura injetado automaticamente, não como um argumento que o Client precisa fornecer — por isso ele é excluído do schema, o que confirmei tanto pelos testes quanto inspecionando a saída do `tools/list` via Inspector.

4. Qual é a vantagem de testar Sampling com um callback stub em vez de sempre precisar de um LLM real configurado?

   Permite validar que o mecanismo do protocolo (a Tool consegue enviar a requisição e receber uma resposta) funciona, sem depender de credenciais externas, custo de API, ou variabilidade de resposta de um LLM real — o teste fica determinístico e rápido.

5. Para que serve, na prática, um Server perguntar ao Client quais Roots estão disponíveis, em vez de simplesmente receber um caminho de diretório como argumento de uma Tool?

   Porque é o Client (que representa o usuário/ambiente local) quem sabe quais diretórios são relevantes e autorizados para aquela sessão — deixar o Server perguntar em vez de aceitar qualquer caminho como argumento de Tool evita que o Server precise confiar cegamente em um caminho arbitrário vindo de qualquer lugar.

---

## Code Review

**Nota: 8/10**

**Pontos positivos:**
- Uso correto de `ctx: Context` para acessar `ctx.session` sem vazar esse detalhe de implementação para o schema da Tool (verificado tanto por teste quanto pelo Inspector)
- Validação via stub é uma escolha de engenharia deliberada e documentada, não uma limitação escondida
- `resumir_via_sampling` valida o tipo de conteúdo retornado (`isinstance(resultado.content, TextContent)`) em vez de assumir cegamente que será texto — `create_message` também pode retornar imagem/áudio conforme o schema do SDK

**Pontos de atenção:**
- `listar_roots_do_client` não trata o caso de o Client não implementar `list_roots_callback` — nesse cenário a chamada provavelmente propaga um erro de protocolo em vez de uma mensagem amigável explicando que o Client não suporta Roots; ficaria melhor capturando isso e retornando uma mensagem clara
- Nenhum teste cobre o caminho de erro (Client sem os callbacks configurados) — só o caminho feliz foi validado

---

## Perguntas de Entrevista

1. Por que Sampling existe no protocolo em vez de cada Server simplesmente chamar a API de um provedor de LLM diretamente?

   Porque assim o Server não precisa de credenciais próprias de nenhum provedor de LLM, nem escolhe qual modelo usar — quem paga e controla a inferência é o Client/usuário, que já tem essa relação estabelecida com seu próprio LLM. Isso também centraliza custo e políticas de uso do lado do Client, em vez de espalhar chaves de API por cada Server que alguém conectar.

2. Que tipo de risco de segurança/custo o Sampling introduz do ponto de vista do Client, e como você mitigaria isso ao implementar um `sampling_callback` de verdade?

   Um Server malicioso ou com bug poderia gerar requisições de Sampling excessivas (custo de API) ou tentar induzir o LLM a produzir conteúdo indevido via prompt injection. Mitigaria com limites de taxa/custo por sessão, exigindo aprovação explícita do usuário antes de cada Sampling (ou por sessão), e nunca expondo esse callback sem alguma forma de revisão humana em contextos sensíveis.

3. Dado que Roots só *informa* diretórios relevantes (não dá permissão de acesso real ao filesystem), quem é responsável por de fato impor essa fronteira de segurança?

   O próprio sistema operacional/processo do Server, através de permissões de arquivo reais, e o código do Server, que deve validar que qualquer caminho usado está de fato dentro dos Roots informados antes de ler/escrever — Roots é só um contrato de escopo, não um mecanismo de enforcement.

**Nota geral: 9/10**

**Q1 (9/10):** Resposta completa, cobre tanto a questão de credenciais quanto de controle de custo do lado do Client.

**Q2 (9/10):** Identifica riscos reais (custo, prompt injection) e propõe mitigações razoáveis (rate limit, aprovação humana).

**Q3 (9/10):** Resposta correta — reconhece que Roots é um contrato de escopo, não um mecanismo de segurança em si, e que a responsabilidade de validação é do código do Server.
