# Sprint 8 — Projeto Final: Assistente de Repositório Git

**Data:** 2026-07-07
**Status:** Concluída ✅

---

## Objetivo

Construir um MCP Server para um caso de uso real — não mais um exercício isolado por primitiva, mas um server único que combina Tools, Resources e Prompts para um problema genuinamente útil: dar a um LLM acesso de leitura ao histórico e conteúdo de um repositório Git. Como teste final, o server aponta para este próprio repositório.

---

## O que foi construído

Um server chamado `assistente-de-repositorio` (`server.py`), somente leitura (nenhuma Tool modifica o repositório), configurável via `REPO_PATH` (padrão: a raiz deste próprio repositório).

| Primitiva | Nome | O que faz |
|---|---|---|
| Tool | `git_log(limite=10)` | Lista os commits mais recentes (hash, autor, data, mensagem) |
| Tool | `git_status()` | Status atual do working tree |
| Tool | `mostrar_commit(ref="HEAD")` | Mostra um commit especifico, com diff |
| Tool | `buscar_commits_por_autor(autor, limite=10)` | Filtra commits por autor (substring, case-insensitive) |
| Resource | `repo://readme` | Conteúdo do `README.md` da raiz |
| Resource template | `repo://arquivo/{caminho}` | Conteúdo de qualquer arquivo rastreado do repositório |
| Prompt | `resumir_commits_recentes(limite=10)` | Pede um resumo do histórico recente |
| Prompt | `revisar_commit(ref="HEAD")` | Pede uma revisão de código de um commit específico |

---

## Dois bugs reais encontrados e corrigidos

**1. `git log`/`git show` travando indefinidamente.** A primeira versão de `_rodar_git` chamava `subprocess.run(["git", *args], capture_output=True, ...)` sem especificar `stdin`. Ao rodar dentro do server MCP (transporte `stdio`), isso travou a chamada da Tool indefinidamente — nenhum erro, nenhum timeout, só silêncio.

**Causa:** o subprocesso do `git` **herdava o `stdin` do processo do server**, que no transporte `stdio` é o pipe de comunicação com o Client. Isso é diferente de rodar o mesmo código num terminal comum, onde `stdin` é o teclado — por isso o bug só apareceu testando via protocolo MCP de verdade, nunca chamando a função Python isoladamente.

**Correção:** duas mudanças em `_rodar_git`: `"--no-pager"` (evita abrir um pager interativo) e, principalmente, `stdin=subprocess.DEVNULL` (garante que o subprocesso nunca tenta ler de um stdin que na verdade pertence ao protocolo MCP).

**Lição geral:** qualquer subprocesso disparado de dentro de um Server MCP com transporte `stdio` deve declarar explicitamente seu próprio `stdin`/`stdout`/`stderr` — nunca herdar os do processo pai.

**2. Barras não são permitidas dentro de um único parâmetro de Resource template.** `repo://arquivo/{caminho}` funciona para `repo://arquivo/README.md`, mas falha silenciosamente (não casa com o template) para `repo://arquivo/docs/sprints/sprint-01.md` — o SDK gera a regex do template trocando `{caminho}` por `[^/]+`, que por definição não inclui `/`.

**Correção:** o Client codifica as barras do caminho como `%2F` antes de montar o URI (`urllib.parse.quote(caminho, safe="")`), e o Server decodifica com `urllib.parse.unquote(caminho)` antes de resolver o path — validado com um teste que lê `docs%2Fsprints%2Fsprint-01.md` e confirma que o conteúdo do arquivo aninhado volta corretamente.

---

## Arquitetura

```
Client MCP ──stdio──> server.py (assistente-de-repositorio)
                          ├─ Tools    (git_log, git_status, mostrar_commit, buscar_commits_por_autor)
                          │     └─ subprocess.run(["git", "--no-pager", ...], stdin=DEVNULL, cwd=REPO_PATH)
                          ├─ Resource repo://readme
                          ├─ Template repo://arquivo/{caminho}   (barras codificadas como %2F)
                          └─ Prompts  (resumir_commits_recentes, revisar_commit)
```

Segurança: todo acesso a arquivo passa por `_resolver_caminho_no_repo`, que resolve o caminho e confirma (`Path.is_relative_to`) que o resultado continua dentro de `REPO_PATH`, além de bloquear qualquer acesso a `.git/` — nenhuma Tool ou Resource escreve no repositório.

---

## Decisões Arquiteturais

| Decisão | Escolha | Alternativa descartada | Motivo |
|---------|---------|------------------------|--------|
| Caso de uso | Assistente de leitura de repositório Git | Extensão do gerenciador de tarefas (Sprint 2) | Caso de uso genuinamente útil e verificável contra dados reais (o próprio histórico deste repositório), reunindo Tools + Resources + Prompts num único server coerente |
| Escopo das Tools | Somente leitura (`log`, `status`, `show`) | Incluir `commit`/`push`/`checkout` | Um server que qualquer Host pudesse conectar sem risco de alterar o repositório sem intervenção humana explícita |
| Alvo do repositório | `REPO_PATH` configurável, com default apontando para a raiz deste próprio repositório | Caminho fixo/hardcoded | Permite testar contra dados reais sem configuração extra, e reaproveitar o server contra qualquer outro repositório apontando `REPO_PATH` |
| Acesso a arquivo aninhado | Barras codificadas (`%2F`) no URI, decodificadas no Server | Restringir Resources a arquivos da raiz apenas | Preserva a funcionalidade completa (ler qualquer arquivo do repo) em vez de aceitar uma limitação do SDK como teto |
| Isolamento do subprocesso `git` | `stdin=subprocess.DEVNULL` explícito | Deixar o `subprocess.run` herdar o stdin do processo pai (padrão) | Bug real encontrado nesta sprint: herdar o stdin do server trava a chamada indefinidamente sob transporte `stdio` |

---

## Arquivos Criados

| Arquivo/Pasta | Função |
|---|---|
| `docs/sprints/sprint-08.md` | Este documento |
| `servers/sprint-08-final-project/server.py` | Server final: 4 Tools, 1 Resource + 1 template, 2 Prompts |
| `servers/sprint-08-final-project/tests/test_server.py` | 11 testes, incluindo os dois bugs corrigidos e as proteções de segurança |

---

## Conceitos Ensinados

- Um server MCP "de verdade" combina Tools, Resources e Prompts em torno de um único domínio coerente, não uma primitiva isolada por exercício
- Subprocessos disparados de dentro de um server `stdio` precisam de `stdin`/`stdout`/`stderr` explicitamente isolados — herdar os do processo pai pode travar o protocolo
- Resource templates do SDK (`{param}`) não casam com `/` dentro do valor — caminhos aninhados exigem codificação explícita (`%2F`) e decodificação manual
- Validação de path traversal (`Path.resolve()` + `is_relative_to`) é obrigatória sempre que uma Resource expõe leitura de arquivos por caminho fornecido pelo Client
- Testar contra dados reais (o próprio histórico deste repositório) pega bugs que dados fictícios não pegariam — os dois bugs desta sprint só apareceram testando de ponta a ponta, nunca nas funções isoladas

---

## Perguntas de Validação

1. Por que o bug do `git log` travando só apareceu testando via protocolo MCP, e nunca chamando `server.git_log()` diretamente num teste unitário?

   Porque o bug dependia do `stdin` do processo do server ser, especificamente, o pipe de comunicação `stdio` com o Client MCP. Num teste unitário chamando a função Python diretamente no terminal, `stdin` é o teclado/console normal, então o subprocesso do `git` nunca tinha motivo para travar esperando input.

2. O que `stdin=subprocess.DEVNULL` resolve especificamente, e por que isso é particularmente relevante para servers que usam transporte `stdio`?

   Garante que o subprocesso do `git` nunca herde um `stdin` que na verdade pertence a outra coisa (o pipe do protocolo MCP) — ele simplesmente não tem nenhum stdin para ler, então nunca fica esperando input. É particularmente relevante em `stdio` porque é exatamente ali que o `stdin` do processo já está "ocupado" com outro propósito.

3. Por que `repo://arquivo/docs/sprints/sprint-01.md` não funcionaria como URI de Resource, mesmo com o template `repo://arquivo/{caminho}` definido?

   Porque o SDK converte `{caminho}` numa regex `[^/]+`, que não casa com nenhuma barra — um URI com várias barras depois de `arquivo/` simplesmente não bate com o padrão do template, então a Resource não seria encontrada.

4. Que papel `Path.is_relative_to` cumpre em `_resolver_caminho_no_repo`, e o que aconteceria sem essa checagem?

   Ele confirma que, depois de resolver o caminho (inclusive `..`), o resultado continua dentro de `REPO_PATH`. Sem essa checagem, um caminho como `../../../../windows/win.ini` conseguiria escapar do repositório e ler qualquer arquivo acessível ao processo do server — uma vulnerabilidade de path traversal.

5. Por que todas as Tools deste server são somente leitura? O que mudaria na análise de risco se `git_commit`/`git_push` fossem adicionadas?

   Porque um server somente leitura pode ser conectado a qualquer Host sem risco de alterar o repositório de forma automática/inesperada. Adicionar `git_commit`/`git_push` mudaria completamente a análise de risco: passaria a ser necessário considerar autenticação/autorização granular, confirmação explícita do usuário antes de cada ação, e proteção contra um LLM decidir fazer commit/push de forma indevida.

---

## Code Review

**Nota: 9/10**

**Pontos positivos:**
- Dois bugs reais de ambiente (stdin herdado, limitação de barra em Resource template) identificados e corrigidos durante o desenvolvimento, não apenas documentados depois
- Escopo deliberadamente somente-leitura, reduzindo a superfície de risco de um server que qualquer Host poderia conectar
- Validação de path traversal e bloqueio de acesso a `.git/` cobertos por teste, não só por inspeção de código
- Testado contra dados reais (o histórico deste próprio repositório) em vez de fixtures sintéticas, aumentando a confiança de que o server funciona em uso real
- `buscar_commits_por_autor` reaproveita `git_log` em vez de duplicar a lógica de parsing do `git log`

**Pontos de atenção:**
- `buscar_commits_por_autor` busca em até 1000 commits fixos (`git_log(limite=1000)`) antes de filtrar — funciona bem para este repositório, mas não escalaria bem para um repositório com histórico muito maior; o ideal seria filtrar diretamente no `git log --author=...`
- `REPO_PATH` aceita qualquer diretório passado via variável de ambiente sem validar que é de fato um repositório Git — uma chamada a um diretório errado falha só na primeira chamada ao `git`, não na inicialização do server

---

## Perguntas de Entrevista

1. Este server só tem Tools de leitura. Se você precisasse adicionar uma Tool `criar_branch`, que salvaguardas você colocaria antes de liberar isso para um Host qualquer?

   Exigiria autenticação com scope específico para operações de escrita (reaproveitando o mecanismo da Sprint 7), validaria o nome da branch contra um padrão seguro (evitando injeção de argumentos no `git`), e adicionaria uma etapa de confirmação explícita — por exemplo, retornando uma prévia da ação e só executando de fato numa segunda chamada, em vez de criar a branch imediatamente na primeira invocação do modelo.

2. Como você generalizaria `_resolver_caminho_no_repo` para reutilizar em outro server que também precise expor leitura de arquivos de forma segura?

   Extrairia a função para um módulo utilitário reutilizável, parametrizado pelo diretório raiz permitido (em vez de depender de `REPO_PATH` fixo), e a reaproveitaria em qualquer server que precise resolver e validar caminhos fornecidos pelo Client contra uma raiz específica.

3. Dado tudo que foi construído nas 8 sprints, qual primitiva ou conceito você escolheria aprofundar em seguida, e por quê?

   Aprofundaria autenticação/autorização granular por scope (mencionada mas não totalmente implementada na Sprint 7) e Sampling com um LLM real (só validado com stub na Sprint 6) — são os dois pontos onde o exercício ficou mais simplificado em relação a um cenário de produção completo.

**Nota geral: 9/10**

**Q1 (9/10):** Resposta completa, combina autenticação por scope, validação de entrada e um padrão de confirmação em duas etapas — mostra raciocínio de defesa em profundidade.

**Q2 (9/10):** Identifica corretamente o parâmetro que precisa ser generalizado (a raiz permitida) para tornar a função reutilizável.

**Q3 (9/10):** Escolhas coerentes com as próprias limitações documentadas nas Sprints 6 e 7 — mostra que as lacunas registradas ao longo do estudo foram internalizadas, não só anotadas.
