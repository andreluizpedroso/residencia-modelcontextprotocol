from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts.base import UserMessage

mcp = FastMCP("biblioteca-de-notas")

_notes: dict[str, dict[str, str]] = {
    "mcp-intro": {
        "titulo": "Introducao ao MCP",
        "conteudo": (
            "O Model Context Protocol (MCP) padroniza como aplicacoes de IA se conectam "
            "a ferramentas e fontes de dados, evitando integracoes proprietarias para "
            "cada combinacao de aplicacao e ferramenta."
        ),
    },
    "json-rpc": {
        "titulo": "JSON-RPC 2.0",
        "conteudo": (
            "JSON-RPC 2.0 e um protocolo leve para chamadas remotas de funcao, "
            "representado em JSON: uma requisicao tem 'method' e 'params', e a "
            "resposta tem 'result' ou 'error'. E o formato de mensagem usado pelo MCP."
        ),
    },
    "uv-cheatsheet": {
        "titulo": "uv - comandos essenciais",
        "conteudo": (
            "uv init cria um projeto novo. uv add instala uma dependencia. "
            "uv run executa um script dentro do ambiente do projeto. "
            "uv sync instala as dependencias travadas no uv.lock."
        ),
    },
}


@mcp.resource("notes://list")
def listar_notas() -> list[dict[str, str]]:
    """Lista o id e o titulo de todas as notas disponiveis."""
    return [{"id": nid, "titulo": nota["titulo"]} for nid, nota in _notes.items()]


@mcp.resource("notes://{note_id}")
def ler_nota(note_id: str) -> str:
    """Retorna o conteudo completo de uma nota pelo ID."""
    nota = _notes.get(note_id)
    if nota is None:
        raise ValueError(f"Nota '{note_id}' nao encontrada")
    return nota["conteudo"]


@mcp.prompt()
def resumir_nota(note_id: str) -> str:
    """Gera um prompt pedindo um resumo objetivo da nota indicada."""
    nota = _notes.get(note_id)
    if nota is None:
        raise ValueError(f"Nota '{note_id}' nao encontrada")
    return (
        f"Resuma a nota '{nota['titulo']}' abaixo em ate 3 frases, mantendo "
        f"apenas as informacoes essenciais:\n\n{nota['conteudo']}"
    )


@mcp.prompt()
def revisar_nota(note_id: str, foco: str = "clareza") -> list[UserMessage]:
    """Gera um prompt pedindo revisao da nota com foco especifico (ex: clareza, precisao tecnica)."""
    nota = _notes.get(note_id)
    if nota is None:
        raise ValueError(f"Nota '{note_id}' nao encontrada")
    return [
        UserMessage(
            f"Revise a nota '{nota['titulo']}' com foco em {foco}. Aponte "
            f"problemas especificos e sugira uma reescrita quando necessario.\n\n"
            f"{nota['conteudo']}"
        )
    ]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
