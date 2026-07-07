import argparse
import asyncio
import json
import shlex

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def parse_value(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def parse_kv_pairs(pairs: list[str]) -> dict:
    return dict(pair.split("=", 1) for pair in pairs)


async def listar_capacidades(session: ClientSession) -> None:
    tools = await session.list_tools()
    resources = await session.list_resources()
    templates = await session.list_resource_templates()
    prompts = await session.list_prompts()

    print("Tools:", [t.name for t in tools.tools])
    print("Resources:", [str(r.uri) for r in resources.resources])
    print("Resource templates:", [t.uriTemplate for t in templates.resourceTemplates])
    print("Prompts:", [p.name for p in prompts.prompts])


async def chamar_tool(session: ClientSession, tool_name: str, kv_pairs: list[str]) -> bool:
    tool_args = {k: parse_value(v) for k, v in parse_kv_pairs(kv_pairs).items()}
    result = await session.call_tool(tool_name, tool_args)
    for block in result.content:
        print(getattr(block, "text", block))
    return result.isError


async def ler_resource(session: ClientSession, uri: str) -> None:
    result = await session.read_resource(uri)
    for content in result.contents:
        print(content.text)


async def obter_prompt(session: ClientSession, prompt_name: str, kv_pairs: list[str]) -> None:
    prompt_args = parse_kv_pairs(kv_pairs)
    result = await session.get_prompt(prompt_name, prompt_args)
    for message in result.messages:
        print(f"[{message.role}] {message.content.text}")


async def run(command: str, server_args: list[str], action: str, extra: list[str]) -> int:
    params = StdioServerParameters(command=command, args=server_args)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            if action == "list":
                await listar_capacidades(session)
            elif action == "call":
                tool_name, *kv_pairs = extra
                is_error = await chamar_tool(session, tool_name, kv_pairs)
                return 1 if is_error else 0
            elif action == "read":
                (uri,) = extra
                await ler_resource(session, uri)
            elif action == "prompt":
                prompt_name, *kv_pairs = extra
                await obter_prompt(session, prompt_name, kv_pairs)
            else:
                raise ValueError(f"Acao desconhecida: {action}")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Client MCP customizado (stdio)")
    parser.add_argument(
        "--server",
        required=True,
        help='Comando para subir o server, entre aspas (ex: "uv run server.py")',
    )
    parser.add_argument("action", choices=["list", "call", "read", "prompt"])
    parser.add_argument(
        "extra", nargs="*", help="Argumentos da acao (ex: nome_da_tool chave=valor ...)"
    )
    args = parser.parse_args()

    command, *server_args = shlex.split(args.server)
    exit_code = asyncio.run(run(command, server_args, args.action, args.extra))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
