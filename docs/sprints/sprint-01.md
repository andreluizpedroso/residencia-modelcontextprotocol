# Sprint 1 — Fundamentos do MCP + Setup do Ambiente

**Data:** 2026-07-07
**Status:** Concluída ✅

---

## Objetivo

Entender, do zero, o que é o Model Context Protocol (MCP), por que ele existe, e deixar o ambiente de desenvolvimento pronto para construir o primeiro server nas próximas sprints.

---

## O problema que o MCP resolve

Modelos de linguagem (LLMs) são poderosos, mas isolados: sozinhos, não sabem ler arquivos, consultar um banco de dados, chamar uma API interna ou executar uma ação num sistema. Antes do MCP, cada aplicação de IA (Claude Desktop, um IDE, um chatbot interno) que quisesse se conectar a cada ferramenta (GitHub, Drive, Postgres, Slack) precisava de uma integração sob medida — problema de combinação **N aplicações × M ferramentas**.

O MCP define um **protocolo padrão único**: qualquer aplicação que "fale MCP" conecta em qualquer ferramenta que "fale MCP", sem integração proprietária. Analogia: MCP é a USB-C das aplicações de IA — um conector físico único no lugar de um plugue por fabricante.

---

## Arquitetura

```
Usuário → Host (com o LLM) → Client MCP #1 → Server MCP A (ex: filesystem)
                            → Client MCP #2 → Server MCP B (ex: GitHub)
```

- **Host**: aplicação que o usuário usa, contém o LLM, decide quando acionar o MCP (ex: Claude Desktop).
- **Client**: vive dentro do Host, mantém conexão **1:1** com exatamente um Server.
- **Server**: processo (local ou remoto) que expõe capacidades via protocolo MCP. É o que construímos nesta e nas próximas sprints.

Um Server expõe três primitivas:

- **Tools** — funções que o modelo decide chamar (ações, com efeitos colaterais).
- **Resources** — dados legíveis, sem efeito colateral (como um `GET`).
- **Prompts** — templates de instrução reutilizáveis, disparados pelo usuário.

Por baixo dos panos, as mensagens são **JSON-RPC 2.0**, trafegando sobre `stdio` (processo local — usado nesta e na próxima sprint) ou HTTP (remoto — Sprint 7).

---

## Decisões Arquiteturais

| Decisão | Escolha | Alternativa descartada | Motivo |
|---------|---------|------------------------|--------|
| SDK | `mcp` (Python SDK oficial) | Implementar JSON-RPC na mão | SDK já implementa protocolo e transporte; foco fica em definir tools/resources, não reinventar o protocolo |
| Gerenciador de projeto | `uv` | pip + requirements.txt | Lock file (`uv.lock`), resolução rápida, mesmo padrão usado no `residencia-mle-mlops` |
| Layout do código | 1 projeto `uv` independente por sprint (`servers/sprint-NN-*/`) | 1 workspace único compartilhado | Cada sprint introduz dependências/conceitos novos isoladamente; evita acoplar exercícios de sprints diferentes |
| Versão do Python | 3.12 | 3.10 (já instalado globalmente) | Alinhado ao badge do README e ao padrão do `residencia-mle-mlops`; `uv` resolve e baixa automaticamente |
| Transporte inicial | `stdio` | HTTP | Mais simples para aprender; recomenda-se começar local antes de ir para remoto (Sprint 7) |

---

## Arquivos Criados

| Arquivo/Pasta | Função |
|---|---|
| `docs/sprints/sprint-01.md` | Este documento |
| `servers/sprint-01-hello-mcp/pyproject.toml` | Definição do projeto + dependência `mcp>=1.28.1` |
| `servers/sprint-01-hello-mcp/main.py` | Script mínimo: importa o SDK `mcp` e confirma a versão instalada |
| `servers/sprint-01-hello-mcp/.python-version` | Pin da versão do Python (3.12) para o `uv` |
| `servers/sprint-01-hello-mcp/.gitignore` | Ignora `.venv/` e `__pycache__/` |
| `CLAUDE.md` | Guia de arquitetura e comandos do repositório para o Claude Code |

---

## Conceitos Ensinados

- Problema de N×M integrações que motivou a criação do MCP
- Arquitetura Host / Client / Server e a relação 1:1 entre Client e Server
- As três primitivas de um Server: Tools (ação), Resources (leitura, sem efeito colateral), Prompts (templates)
- JSON-RPC 2.0 como formato de mensagem por baixo do protocolo
- Transportes disponíveis: `stdio` (local) vs HTTP (remoto)
- SDK oficial Python (`mcp`) como camada que abstrai o protocolo

---

## Perguntas de Validação

1. Por que o MCP existe? Que problema, na prática, ele evita que cada equipe resolva sozinha?

   O MCP existe para padronizar a forma como aplicações de IA se conectam a ferramentas e dados. Sem ele, cada equipe teria de criar integrações proprietárias e customizadas para cada sistema, o que gera um problema de multiplicação de esforço e manutenção em cenários de N aplicações × M ferramentas.

2. Qual a diferença de responsabilidade entre Host, Client e Server?

   O Host é a aplicação que o usuário usa e que contém o LLM; ele decide quando usar o MCP. O Client é a ponta do Host que mantém a conexão com um Server específico. O Server é o componente que expõe capacidades, como tools, resources e prompts, para o Host acessar.

3. Se um Host precisa se conectar a dois servers diferentes, quantos Clients ele cria? Por quê?

   Ele cria dois Clients, porque a relação entre Client e Server é 1:1. Cada Client representa uma conexão específica com um único Server.

4. Qual a diferença entre uma Tool e um Resource? Dê um exemplo de cada que não esteja neste documento.

   Uma Tool representa uma ação que pode ser executada, normalmente com efeito colateral, como criar algo ou disparar uma operação. Um Resource representa dados legíveis, sem efeito colateral, que podem ser consultados. Exemplo de Tool: "criar um ticket no Jira". Exemplo de Resource: "listar os últimos 10 commits de um repositório".

5. Que formato de mensagem o MCP usa por baixo dos panos, e sobre quais transportes ele pode trafegar?

   O MCP usa JSON-RPC 2.0 por baixo dos panos. Ele pode trafegar sobre stdio, para comunicação local via processo, e sobre HTTP, para comunicação remota.

---

## Code Review

**Nota: 8/10**

O único código desta sprint é `servers/sprint-01-hello-mcp/main.py`, um script de validação do ambiente (não um Server MCP de verdade — isso começa na Sprint 2).

**Pontos positivos:**
- Usa `importlib.metadata.version("mcp")` em vez de um atributo `__version__` hardcoded/inexistente — forma correta de checar a versão de um pacote instalado
- `.gitignore` do projeto já criado corretamente, evitando versionar `.venv/`

**Pontos de atenção:**
- Script é só um smoke test manual — não há teste automatizado (`pytest`) ainda; aceitável nesta sprint, mas o padrão do `residencia-mle-mlops` (`tests/test_smoke.py`) sugere introduzir testes automatizados já a partir da Sprint 2, quando houver um Server de verdade para testar

---

## Perguntas de Entrevista

1. Um recrutador pergunta: "o que é o MCP e por que ele importa?" — responda como se fosse essa entrevista, em poucas frases.

   O MCP é um padrão aberto para conectar aplicações de IA a ferramentas e dados de forma interoperável. Ele importa porque reduz a complexidade de integrações sob medida e torna mais simples escalar soluções com LLMs em ambientes reais.

2. Qual a diferença prática entre um Server MCP rodando via `stdio` e um rodando via HTTP? Em que cenário você escolheria cada um?

   Um Server via `stdio` roda localmente, geralmente junto ao Host, e é mais adequado para integrações simples e rápidas em um ambiente de desktop ou desenvolvimento local. Um Server via HTTP é mais apropriado quando a capacidade precisa ficar disponível remotamente, para vários clientes ou em cenários com rede, autenticação e escalabilidade.

3. Por que uma Tool não deveria ser usada para expor dados somente-leitura, se um Resource já existe para isso?

   Porque Tool sugere ação e possivelmente efeito colateral, enquanto Resource é a abstração semântica correta para consulta de dados. Usar Tool para leitura só torna a interface menos clara, menos previsível e mais difícil de explorar e otimizar.

---

**Nota geral: 8.5/10**

**Q1 (9/10):** Resposta correta e concisa — cobre o "o quê" (padrão aberto, interoperabilidade) e o "porquê" (menos complexidade de integração, mais escala). Numa entrevista real, reforçaria com um exemplo concreto (ex: Claude Desktop e servers de terceiros já falando o mesmo protocolo).

**Q2 (8/10):** Distinção correta entre uso local/simples (`stdio`) e remoto/multi-cliente (HTTP). Gap: não menciona a diferença de modelo de confiança — `stdio` roda com os mesmos privilégios do processo Host, sem autenticação de rede; HTTP exige lidar com autenticação, TLS e gerenciamento de sessão, tema que volta com força na Sprint 7.

**Q3 (9/10):** Resposta sólida — identifica a semântica (ação vs. leitura) e já aponta a consequência prática (menos previsível, mais difícil de otimizar). Ponto a acrescentar: Resources também podem ser listados e pré-carregados pelo Host sem o modelo precisar "decidir" chamar nada, o que uma Tool não permite.
