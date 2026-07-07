import asyncio

import mcp.types as types
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def sampling_stub(context, params: types.CreateMessageRequestParams) -> types.CreateMessageResult:
    """Simula o LLM do Client: em vez de chamar um modelo de verdade, devolve
    uma resposta previsivel para provar que o round-trip Server -> Client -> Server
    funciona."""
    ultima_mensagem = params.messages[-1].content.text
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(type="text", text=f"[resumo simulado] {ultima_mensagem[:60]}"),
        model="stub-model",
    )


async def roots_stub(context) -> types.ListRootsResult:
    """Simula o Client expondo um unico Root fixo."""
    return types.ListRootsResult(
        roots=[types.Root(uri="file:///C:/projeto-exemplo/", name="projeto-exemplo")]
    )


async def _run_tool(tool_name: str, arguments: dict) -> types.CallToolResult:
    params = StdioServerParameters(command="uv", args=["run", "server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(
            read,
            write,
            sampling_callback=sampling_stub,
            list_roots_callback=roots_stub,
        ) as session:
            await session.initialize()
            return await session.call_tool(tool_name, arguments)


async def _list_tool_names() -> list[str]:
    params = StdioServerParameters(command="uv", args=["run", "server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [t.name for t in result.tools]


def test_tools_nao_expoem_o_parametro_ctx():
    nomes = asyncio.run(_list_tool_names())
    assert set(nomes) == {"resumir_via_sampling", "listar_roots_do_client"}


def test_resumir_via_sampling_usa_resposta_do_client():
    result = asyncio.run(
        _run_tool("resumir_via_sampling", {"texto": "MCP padroniza integracoes de IA com ferramentas."})
    )

    assert not result.isError
    assert "[resumo simulado]" in result.content[0].text


def test_listar_roots_do_client_retorna_o_root_exposto():
    result = asyncio.run(_run_tool("listar_roots_do_client", {}))

    assert not result.isError
    assert "projeto-exemplo" in result.content[0].text
