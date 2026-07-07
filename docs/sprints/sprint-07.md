# Sprint 7 — Transporte Remoto (HTTP) & Autenticação

**Data:** 2026-07-07
**Status:** Concluída ✅

---

## Objetivo

Sair do transporte `stdio` (processo local, usado desde a Sprint 2) e rodar um Server MCP sobre **HTTP** (`streamable-http`), protegido por **autenticação Bearer token** — o cenário de um server remoto de verdade, acessível por múltiplos Clients pela rede.

---

## O que foi construído

Um server chamado `servidor-remoto-autenticado` (`server.py`), com uma Tool (`somar`), rodando em `http://127.0.0.1:8765/mcp` via `mcp.run(transport="streamable-http")`, exigindo um Bearer token válido em toda requisição.

Autenticação implementada com um `TokenVerifier` customizado — **não** um Authorization Server OAuth completo (ver Decisões Arquiteturais):

```python
class VerificadorDeTokenFixo(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        if token != TOKEN_VALIDO:
            return None
        return AccessToken(token=token, client_id="cliente-de-estudo", scopes=[...])

mcp = FastMCP(
    "servidor-remoto-autenticado",
    token_verifier=VerificadorDeTokenFixo(),
    auth=AuthSettings(issuer_url="https://auth.exemplo.local", resource_server_url="http://127.0.0.1:8765", ...),
    host="127.0.0.1", port=8765,
)
```

---

## Validação

Testado com o server subindo como subprocesso real (`subprocess.Popen`), aguardando a porta abrir, e usando o Client HTTP do SDK:

| Cenário | Resultado |
|---|---|
| Sem header `Authorization` | Requisição rejeitada (comprovado tanto via `curl` cru — `401 Unauthorized` com `WWW-Authenticate: Bearer error="invalid_token"` — quanto via Client do SDK) |
| Token errado | Requisição rejeitada, mesmo comportamento |
| Token correto (`Bearer segredo-da-sprint-7`) | Tool `somar` executa normalmente, resposta `5` |

---

## Duas lições de ambiente encontradas nesta sprint

**1. API depreciada silenciosamente trocada.** A primeira versão dos testes usava `streamablehttp_client(url, headers=..., ...)` — funcionava, mas emitia `DeprecationWarning: Use streamable_http_client instead`. A API nova (`streamable_http_client`) não aceita mais `headers`/`auth` diretamente: espera que você construa seu próprio `httpx.AsyncClient(headers=...)` e passe via `http_client=`. Migrado para a API nova — motivo a mais para sempre rodar os testes e prestar atenção em warnings, não só em falhas.

**2. `uv run <script>` no Windows não mata o processo filho ao receber `terminate()`.** Igual ao que já tinha acontecido com o `npx` na Sprint 4: `uv run server.py` sobe um processo `uv` que, no Windows, spawna um processo Python **filho** em vez de substituir a si mesmo (`exec`). Chamar `.terminate()` no processo do `uv` deixava o Python filho vivo, segurando a porta 8765 — o próximo teste falhava ao tentar subir o server de novo (`[Errno 10048] endereço já em uso`). Corrigido usando `taskkill /PID <pid> /T /F` (mata a árvore de processos inteira) em vez de `Popen.terminate()`.

Os dois achados foram corrigidos no código final; nenhum dos dois é um problema do MCP em si — são detalhes de como wrappers de processo (`uv run`, `npx`) se comportam no Windows.

---

## Arquitetura

```
Client (SDK)  ──HTTP POST /mcp──►  uvicorn (streamable-http)
   Authorization: Bearer <token>         │
                                          ▼
                            FastMCP.token_verifier.verify_token(token)
                                          │
                      token invalido ──► 401 Unauthorized (WWW-Authenticate: Bearer)
                      token valido   ──► segue para a Tool normalmente
```

Diferença central para `stdio`: aqui existe uma fronteira de rede real, então autenticação deixa de ser opcional — qualquer processo que saiba o endereço pode tentar se conectar.

---

## Decisões Arquiteturais

| Decisão | Escolha | Alternativa descartada | Motivo |
|---------|---------|------------------------|--------|
| Transporte | `streamable-http` | `sse` (também disponível no SDK) | `streamable-http` é o transporte HTTP recomendado atualmente pelo SDK; `sse` é o transporte HTTP legado, mantido por compatibilidade |
| Autenticação | `TokenVerifier` customizado com um token fixo | Authorization Server OAuth 2.1 completo | Implementar um Authorization Server de verdade (metadata, PKCE, dynamic client registration) é um tópico à parte; o objetivo aqui é entender o **mecanismo de verificação de Bearer token** no lado do Resource Server, que é o mesmo independente de quem emitiu o token |
| `issuer_url` | Valor placeholder (`https://auth.exemplo.local`), nunca acessado de verdade | Rodar um servidor de autorização real na mesma máquina | Nosso `verify_token` nunca consulta o `issuer_url` — ele só aparece nos metadados/erro `WWW-Authenticate`, então um placeholder é suficiente para o exercício |
| Cliente HTTP nos testes | `streamable_http_client` + `httpx.AsyncClient(headers=...)` | `streamablehttp_client` (API antiga, com `headers=` direto) | A API antiga está deprecated; migramos para a atual assim que o warning apareceu |
| Encerramento do processo do server nos testes | `taskkill /PID <pid> /T /F` | `Popen.terminate()` | No Windows, `uv run` deixa órfão o processo Python filho ao receber só um `terminate()` no processo do `uv` |

---

## Arquivos Criados

| Arquivo/Pasta | Função |
|---|---|
| `docs/sprints/sprint-07.md` | Este documento |
| `servers/sprint-07-http-auth/server.py` | Server HTTP com autenticação Bearer via `TokenVerifier` |
| `servers/sprint-07-http-auth/tests/test_http_auth.py` | Testes de integração reais: sem token, token inválido, token válido |

---

## Conceitos Ensinados

- `mcp.run(transport="streamable-http")` sobe o server como uma aplicação HTTP (uvicorn) em vez de falar `stdio`
- Autenticação em MCP sobre HTTP funciona no nível de Resource Server: um `TokenVerifier` decide se um Bearer token é válido, independente de quem o emitiu
- Uma requisição sem token válido recebe `401 Unauthorized` com um header `WWW-Authenticate` apontando para onde obter um token (`resource_metadata`)
- `AuthSettings.issuer_url` é metadado, não uma dependência de rede em tempo real — nosso `verify_token` nunca precisa chamá-lo
- Wrappers de processo (`uv run`, `npx`) podem deixar processos filhos órfãos no Windows ao serem apenas "terminados"; matar a árvore inteira (`taskkill /T`) é mais robusto

---

## Perguntas de Validação

> *(A preencher com as respostas do usuário)*

1. O que muda arquiteturalmente ao trocar o transporte de `stdio` para `streamable-http`, além do meio de transporte em si?
2. Por que o `issuer_url` do `AuthSettings` pôde ser um valor fictício, nunca de fato acessado pelo nosso código?
3. O que o cabeçalho `WWW-Authenticate` retornado no `401` comunica ao Client, na prática?
4. Por que a primeira versão dos testes usava uma API que emitia um `DeprecationWarning`, e o que isso ensina sobre rodar testes com atenção aos warnings, não só ao resultado pass/fail?
5. Por que `Popen.terminate()` não foi suficiente para encerrar o server nos testes no Windows, e o que `taskkill /T` faz de diferente?

---

## Code Review

**Nota: 8.5/10**

**Pontos positivos:**
- Testa os três cenários relevantes de autenticação (sem token, token errado, token certo), não só o caminho feliz
- Migrou de uma API deprecated para a atual assim que o warning apareceu, em vez de ignorá-lo
- Resolveu um problema real e específico de plataforma (processo órfão no Windows) em vez de mascarar com um `time.sleep` maior ou ignorar
- Fixture do server usa polling real de porta (`socket.connect_ex`) para saber quando o server está pronto, em vez de um `sleep` fixo arriscado

**Pontos de atenção:**
- O token fixo (`TOKEN_VALIDO`) está hardcoded no código-fonte do server — aceitável para o exercício, mas seria a primeira coisa a mover para variável de ambiente/secret antes de qualquer uso real
- `_porta_aberta()` só confirma que a porta aceita conexões TCP, não que o endpoint `/mcp` já está pronto para falar o protocolo MCP — funcionou nos testes, mas é uma verificação um pouco mais fraca do que checar a resposta HTTP em si

---

## Perguntas de Entrevista

> *(A preencher com as respostas do usuário)*

1. Por que autenticação é opcional em `stdio` mas praticamente obrigatória em HTTP, do ponto de vista de modelo de ameaça?
2. Se você precisasse integrar este server com um Authorization Server OAuth de verdade (ex: Auth0, Okta), o que mudaria no código — e o que **não** mudaria?
3. Por que confiar apenas na presença de um Bearer token não é suficiente para autorização granular (ex: "este cliente só pode chamar tools de leitura")? Que papel os `scopes` do `AccessToken` cumprem aqui?
