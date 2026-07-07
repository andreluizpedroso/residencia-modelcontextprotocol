import asyncio
import socket
import subprocess
import time
from pathlib import Path

import httpx
import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}/mcp"
TOKEN_VALIDO = "segredo-da-sprint-7"
PROJECT_DIR = Path(__file__).resolve().parent.parent


def _porta_aberta() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((HOST, PORT)) == 0


@pytest.fixture(scope="module")
def servidor_http():
    processo = subprocess.Popen(
        ["uv", "run", "server.py"],
        cwd=PROJECT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        for _ in range(100):
            if _porta_aberta():
                break
            time.sleep(0.1)
        else:
            processo.terminate()
            raise RuntimeError("Server HTTP nao subiu a tempo")
        yield
    finally:
        # No Windows, "uv run" spawna um processo filho (o interpretador
        # Python de verdade); terminar so o processo do "uv" nao mata o
        # filho, que continua com a porta aberta. "taskkill /T" mata a
        # arvore inteira.
        subprocess.run(
            ["taskkill", "/PID", str(processo.pid), "/T", "/F"],
            capture_output=True,
        )
        processo.wait(timeout=5)


async def _chamar_somar(headers: dict[str, str]):
    async with httpx.AsyncClient(headers=headers) as http_client:
        async with streamable_http_client(URL, http_client=http_client) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.call_tool("somar", {"a": 2, "b": 3})


def test_requisicao_sem_token_e_rejeitada(servidor_http):
    with pytest.raises(BaseException):
        asyncio.run(_chamar_somar({}))


def test_requisicao_com_token_invalido_e_rejeitada(servidor_http):
    with pytest.raises(BaseException):
        asyncio.run(_chamar_somar({"Authorization": "Bearer token-errado"}))


def test_requisicao_com_token_valido_funciona(servidor_http):
    result = asyncio.run(_chamar_somar({"Authorization": f"Bearer {TOKEN_VALIDO}"}))

    assert not result.isError
    assert result.content[0].text == "5"
