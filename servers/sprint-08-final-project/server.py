import os
import subprocess
from pathlib import Path
from urllib.parse import unquote

from mcp.server.fastmcp import FastMCP

REPO_PATH = Path(os.environ.get("REPO_PATH", Path(__file__).resolve().parents[2])).resolve()

mcp = FastMCP("assistente-de-repositorio")


def _rodar_git(*args: str) -> str:
    # --no-pager evita que "git log"/"git show" tentem abrir um pager
    # interativo. stdin=DEVNULL evita que o subprocesso do git herde o
    # stdin do server (que, no transporte stdio, e o pipe de comunicacao
    # com o Client) e trave esperando input de algum prompt.
    resultado = subprocess.run(
        ["git", "--no-pager", *args],
        cwd=REPO_PATH,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
    )
    if resultado.returncode != 0:
        raise ValueError(f"git {' '.join(args)} falhou: {resultado.stderr.strip()}")
    return resultado.stdout


def _resolver_caminho_no_repo(caminho: str) -> Path:
    alvo = (REPO_PATH / caminho).resolve()
    if not alvo.is_relative_to(REPO_PATH):
        raise ValueError(f"Caminho fora do repositorio: {caminho!r}")
    if ".git" in alvo.parts:
        raise ValueError("Nao e permitido ler arquivos internos do .git")
    return alvo


@mcp.tool()
def git_log(limite: int = 10) -> list[dict]:
    """Lista os commits mais recentes do repositorio (hash, autor, data, mensagem)."""
    saida = _rodar_git(
        "log", f"-n{limite}", "--pretty=format:%H\x1f%an\x1f%ad\x1f%s", "--date=short"
    )
    commits = []
    for linha in saida.splitlines():
        if not linha:
            continue
        hash_, autor, data, mensagem = linha.split("\x1f")
        commits.append({"hash": hash_, "autor": autor, "data": data, "mensagem": mensagem})
    return commits


@mcp.tool()
def git_status() -> str:
    """Retorna o status atual do working tree (git status --porcelain)."""
    return _rodar_git("status", "--porcelain", "--branch")


@mcp.tool()
def mostrar_commit(ref: str = "HEAD") -> str:
    """Mostra as mudancas de um commit especifico (git show), incluindo diff."""
    return _rodar_git("show", ref)


@mcp.tool()
def buscar_commits_por_autor(autor: str, limite: int = 10) -> list[dict]:
    """Busca commits de um autor especifico pelo nome (case-insensitive, substring)."""
    todos = git_log(limite=1000)
    filtrados = [c for c in todos if autor.lower() in c["autor"].lower()]
    return filtrados[:limite]


@mcp.resource("repo://readme")
def ler_readme() -> str:
    """Retorna o conteudo do README.md na raiz do repositorio."""
    caminho = _resolver_caminho_no_repo("README.md")
    if not caminho.exists():
        raise ValueError("README.md nao encontrado na raiz do repositorio")
    return caminho.read_text(encoding="utf-8")


@mcp.resource("repo://arquivo/{caminho}")
def ler_arquivo(caminho: str) -> str:
    """Retorna o conteudo de um arquivo do repositorio, dado seu caminho relativo.

    O template de Resource (`{caminho}`) so combina com um unico segmento de
    URI, sem barras (o SDK usa `[^/]+` na regex gerada). Para expor arquivos
    em subpastas, o caminho e enviado com as barras codificadas (`%2F`) e
    decodificado aqui.
    """
    caminho_real = unquote(caminho)
    alvo = _resolver_caminho_no_repo(caminho_real)
    if not alvo.is_file():
        raise ValueError(f"Arquivo nao encontrado: {caminho_real!r}")
    return alvo.read_text(encoding="utf-8", errors="replace")


@mcp.prompt()
def resumir_commits_recentes(limite: int = 10) -> str:
    """Gera um prompt pedindo um resumo dos commits mais recentes do repositorio."""
    commits = git_log(limite=limite)
    linhas = "\n".join(f"- {c['data']} ({c['autor']}): {c['mensagem']}" for c in commits)
    return (
        f"Resuma, em um paragrafo, o que foi feito nos {limite} commits mais recentes "
        f"deste repositorio:\n\n{linhas}"
    )


@mcp.prompt()
def revisar_commit(ref: str = "HEAD") -> str:
    """Gera um prompt pedindo revisao de codigo de um commit especifico."""
    diff = mostrar_commit(ref)
    return (
        f"Revise as mudancas do commit '{ref}' abaixo. Aponte problemas de "
        f"corretude, simplificacao possivel, e o que esta bem feito:\n\n{diff}"
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
