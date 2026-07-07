from mcp.server.fastmcp import Context, FastMCP
from mcp.types import SamplingMessage, TextContent

mcp = FastMCP("sampling-e-roots")


@mcp.tool()
async def resumir_via_sampling(texto: str, ctx: Context) -> str:
    """Pede ao Client, via Sampling, para gerar um resumo de uma frase do texto."""
    resultado = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(type="text", text=f"Resuma em uma frase: {texto}"),
            )
        ],
        max_tokens=200,
    )
    if isinstance(resultado.content, TextContent):
        return resultado.content.text
    raise ValueError("Sampling nao retornou conteudo de texto")


@mcp.tool()
async def listar_roots_do_client(ctx: Context) -> list[dict]:
    """Pergunta ao Client quais Roots (diretorios/URIs relevantes) ele expoe."""
    resultado = await ctx.session.list_roots()
    return [{"uri": str(root.uri), "nome": root.name} for root in resultado.roots]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
