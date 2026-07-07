from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gerenciador-de-tarefas")


@dataclass
class Task:
    id: int
    titulo: str
    concluida: bool = False


_tasks: dict[int, Task] = {}
_next_id = 1


@mcp.tool()
def adicionar_tarefa(titulo: str) -> str:
    """Adiciona uma nova tarefa a lista e retorna seu ID."""
    global _next_id
    task = Task(id=_next_id, titulo=titulo)
    _tasks[task.id] = task
    _next_id += 1
    return f"Tarefa #{task.id} criada: {titulo!r}"


@mcp.tool()
def listar_tarefas(apenas_pendentes: bool = False) -> list[dict]:
    """Lista as tarefas cadastradas, opcionalmente filtrando so as pendentes."""
    tasks = _tasks.values()
    if apenas_pendentes:
        tasks = (t for t in tasks if not t.concluida)
    return [{"id": t.id, "titulo": t.titulo, "concluida": t.concluida} for t in tasks]


@mcp.tool()
def concluir_tarefa(id: int) -> str:
    """Marca uma tarefa como concluida pelo ID."""
    task = _tasks.get(id)
    if task is None:
        raise ValueError(f"Tarefa #{id} nao encontrada")
    task.concluida = True
    return f"Tarefa #{id} marcada como concluida"


@mcp.tool()
def remover_tarefa(id: int) -> str:
    """Remove uma tarefa da lista pelo ID."""
    if id not in _tasks:
        raise ValueError(f"Tarefa #{id} nao encontrada")
    del _tasks[id]
    return f"Tarefa #{id} removida"


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
