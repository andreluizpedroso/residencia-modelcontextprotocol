# Sprint 3 — Resources & Prompts

**Data:** 2026-07-07
**Status:** Concluída ✅

---

## Objetivo

Completar as três primitivas de um Server MCP construindo Resources (dados legíveis) e Prompts (templates de instrução), depois de já termos coberto Tools na Sprint 2.

---

## O que foi construído

Um server chamado `biblioteca-de-notas` (`server.py`), com 3 notas fixas em memória, expondo:

| Primitiva | Nome/URI | O que faz |
|---|---|---|
| Resource estática | `notes://list` | Lista `id` e `titulo` de todas as notas |
| Resource template | `notes://{note_id}` | Retorna o conteúdo completo de uma nota pelo ID; erro se não existe |
| Prompt | `resumir_nota(note_id)` | Gera instrução para resumir uma nota em até 3 frases |
| Prompt | `revisar_nota(note_id, foco="clareza")` | Gera instrução para revisar uma nota com foco configurável |

---

## Arquitetura

Resources vêm em duas formas no SDK: **estáticas** (URI fixa, ex: `notes://list`) e **templates** (URI com placeholders, ex: `notes://{note_id}`, onde `{note_id}` casa com o parâmetro da função). O client descobre as duas de formas separadas: `list_resources()` só retorna as estáticas; `list_resource_templates()` retorna os templates. Um resource template só vira um resource "de verdade" quando o client chama `read_resource(uri)` com um URI concreto que casa com o padrão.

Prompts podem retornar um `str` simples (convertido automaticamente em uma mensagem) ou uma lista de `Message`/`UserMessage` quando é preciso mais controle sobre o papel (`role`) de cada mensagem gerada.

```
Client MCP ──stdio──> server.py (FastMCP)
                          ├─ Resource   notes://list
                          ├─ Template   notes://{note_id}
                          ├─ Prompt     resumir_nota
                          └─ Prompt     revisar_nota
```

Validação, como na Sprint 2, em duas camadas: pytest chamando as funções diretamente, e um smoke test com `ClientSession` real cobrindo `list_resources`, `list_resource_templates`, `read_resource`, `list_prompts` e `get_prompt`.

---

## Decisões Arquiteturais

| Decisão | Escolha | Alternativa descartada | Motivo |
|---------|---------|------------------------|--------|
| Modelagem das notas | Resource estática (`notes://list`) + template (`notes://{note_id}`) | Uma única Tool `buscar_nota(id)` | Leitura de dados sem efeito colateral é exatamente o caso de uso que Resources existem para resolver — reforça a diferença conceitual entre Tool e Resource já discutida na Sprint 1 |
| Retorno dos Prompts | `str` em `resumir_nota`, `list[UserMessage]` em `revisar_nota` | Sempre `str` | Mostra as duas formas suportadas pelo SDK — a segunda é necessária quando se quer controlar o `role` da mensagem explicitamente |
| Dados de exemplo | 3 notas fixas sobre o próprio conteúdo do curso (MCP, JSON-RPC, uv) | Dataset externo | Reforça os conceitos das sprints anteriores ao mesmo tempo em que serve de conteúdo de teste |
| Erros | `raise ValueError` também em Resources e Prompts, igual às Tools da Sprint 2 | Um mecanismo de erro diferente por primitiva | Consistência: todas as primitivas do SDK convertem exceção Python em erro do protocolo do mesmo jeito |

---

## Arquivos Criados

| Arquivo/Pasta | Função |
|---|---|
| `docs/sprints/sprint-03.md` | Este documento |
| `servers/sprint-03-resources-prompts/server.py` | Server com 1 resource estática, 1 template e 2 prompts |
| `servers/sprint-03-resources-prompts/tests/test_resources_prompts.py` | Testes unitários das funções |
| `servers/sprint-03-resources-prompts/pyproject.toml` | Dependências + config do pytest |

---

## Conceitos Ensinados

- Diferença entre Resource estática (URI fixa) e Resource template (URI com placeholder que vira parâmetro de função)
- `list_resources()` retorna só as estáticas; `list_resource_templates()` retorna os templates — descoberta separada no protocolo
- Prompts podem retornar `str` (vira uma mensagem automaticamente) ou uma lista de `Message`/`UserMessage` para controle explícito de `role`
- Mesma convenção de erro das Tools (`raise` vira erro do protocolo) se aplica a Resources e Prompts
- Resources e Prompts, assim como Tools, são descobertos pelo Client antes de serem usados (`list_*` antes de `read_resource`/`get_prompt`/`call_tool`)

---

## Perguntas de Validação

1. Qual a diferença entre uma Resource estática e uma Resource template? Dê um exemplo de quando cada uma faz sentido.

   Uma Resource estática tem uma URI fixa e representa um dado único (ex: `notes://list`, a lista completa). Uma Resource template tem uma URI parametrizada (`notes://{note_id}`) e representa uma família de recursos parecidos, endereçados por um identificador — faz sentido quando existem "N" itens do mesmo tipo (uma nota especifica, um arquivo especifico).

2. Por que `list_resources()` não retornou `notes://{note_id}` nesta sprint? Que método retorna os templates?

   Porque `notes://{note_id}` não é uma Resource concreta, é um template — só vira uma Resource real quando alguém substitui `{note_id}` por um valor e chama `read_resource`. Quem lista os templates é `list_resource_templates()`.

3. Quando um Prompt deveria retornar uma lista de `Message`/`UserMessage` em vez de simplesmente uma `str`?

   Quando é preciso controlar explicitamente o `role` de cada mensagem gerada (por exemplo, simular uma troca com múltiplas mensagens, ou marcar explicitamente uma mensagem como vinda do "assistant"). Retornar `str` é suficiente quando basta uma única mensagem de usuário.

4. Por que faz mais sentido modelar a leitura de uma nota como Resource em vez de como Tool, dado o que vimos na Sprint 1 sobre a diferença entre as duas primitivas?

   Porque ler uma nota não tem efeito colateral — é puramente uma consulta de dados, exatamente o caso de uso que Resources existem para cobrir. Usar uma Tool para isso confundiria a semântica (Tools sugerem ação) e tornaria a interface menos previsível para o Host decidir quando usá-la.

5. O mecanismo de erro (`raise ValueError`) é o mesmo para Tools, Resources e Prompts. Por que essa consistência é uma vantagem para quem constrói servers MCP?

   Porque quem escreve o server só precisa aprender um padrão de tratamento de erro, independente da primitiva — reduz a carga cognitiva e o risco de inconsistência (cada primitiva sinalizando erro de um jeito diferente).

---

## Code Review

**Nota: 8/10**

**Pontos positivos:**
- Resource estática e template cobrindo os dois casos de uso reais no mesmo exercício, sem exercício artificial separado para cada
- Reaproveitamento consistente do padrão de erro (`raise ValueError`) já estabelecido na Sprint 2, em vez de inventar um mecanismo novo por primitiva
- Os dois Prompts demonstram as duas formas de retorno suportadas (`str` e `list[UserMessage]`), não só uma
- Smoke test cobre as 5 operações de protocolo relevantes (`list_resources`, `list_resource_templates`, `read_resource` ×2, `list_prompts`, `get_prompt` ×2)

**Pontos de atenção:**
- As notas são hardcoded no módulo — igual ao `dict` em memória da Sprint 2, isso significa que não há forma de adicionar notas novas sem editar o código; aceitável para o exercício, mas seria o próximo ponto a resolver (ex: uma Tool `criar_nota` complementando as Resources de leitura)
- `revisar_nota` não valida o valor de `foco` (aceita qualquer string) — não é um bug, mas é o tipo de validação de entrada que a Sprint 2 já havia sinalizado como pendente

---

## Perguntas de Entrevista

1. Um Host decide pré-carregar todas as notas disponíveis no contexto antes mesmo do usuário pedir. Isso é mais natural com Tools ou com Resources? Por quê?

   Com Resources — elas são desenhadas justamente para leitura sem efeito colateral, o que as torna seguras para o Host buscar proativamente sem depender de uma decisão do modelo. Pré-carregar uma Tool não faria sentido, porque Tools representam ações que o modelo decide disparar deliberadamente.

2. Se você precisasse permitir que o usuário criasse notas novas em tempo de execução, isso seria uma Tool, uma Resource, ou os dois?

   Seria uma Tool (`criar_nota`) para a escrita, mantendo as Resources (`notes://list`, `notes://{note_id}`) só para leitura. Os dois coexistiriam: a Tool tem efeito colateral (cria estado novo), então pertence à primitiva de ação; a leitura continua sendo Resource.

3. Por que a descoberta de capacidades no MCP é separada por tipo (`list_tools`, `list_resources`, `list_resource_templates`, `list_prompts`) em vez de um único `list_capabilities` genérico?

   Porque cada primitiva tem uma semântica e um ciclo de uso diferente para o Client (Tools são chamadas pelo modelo, Resources são lidas, Prompts são disparados pelo usuário) — separar a descoberta deixa explícito para o Client o que ele pode fazer com cada item, em vez de precisar inspecionar um campo "tipo" dentro de uma lista genérica.

**Nota geral: 9/10**

**Q1 (9/10):** Identifica corretamente a ausência de efeito colateral como o motivo que torna Resources seguras para pré-carregamento.

**Q2 (9/10):** Distinção correta entre leitura (Resource) e escrita com efeito colateral (Tool), e reconhece que os dois coexistem no mesmo domínio.

**Q3 (9/10):** Boa resposta — a separação por tipo comunica semântica de uso ao Client. Ponto a acrescentar: também simplifica a paginação e o cache de cada lista independentemente.
