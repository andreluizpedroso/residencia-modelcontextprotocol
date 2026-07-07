from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP

HOST = "127.0.0.1"
PORT = 8765
TOKEN_VALIDO = "segredo-da-sprint-7"


class VerificadorDeTokenFixo(TokenVerifier):
    """Verificador simples para fins didaticos: um unico token fixo,
    sem um Authorization Server OAuth de verdade por tras."""

    async def verify_token(self, token: str) -> AccessToken | None:
        if token != TOKEN_VALIDO:
            return None
        return AccessToken(
            token=token,
            client_id="cliente-de-estudo",
            scopes=["tarefas:ler", "tarefas:escrever"],
        )


mcp = FastMCP(
    "servidor-remoto-autenticado",
    token_verifier=VerificadorDeTokenFixo(),
    auth=AuthSettings(
        issuer_url="https://auth.exemplo.local",
        resource_server_url=f"http://{HOST}:{PORT}",
        required_scopes=["tarefas:ler"],
    ),
    host=HOST,
    port=PORT,
)


@mcp.tool()
def somar(a: int, b: int) -> int:
    """Soma dois numeros. So funciona com um Bearer token valido."""
    return a + b


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
