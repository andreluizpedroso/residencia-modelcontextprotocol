import pytest

import server


@pytest.fixture(autouse=True)
def reset_state():
    server._tasks.clear()
    server._next_id = 1
    yield


def test_adicionar_tarefa_cria_com_id_sequencial():
    server.adicionar_tarefa("Estudar MCP")
    server.adicionar_tarefa("Escrever testes")

    tarefas = server.listar_tarefas()

    assert [t["id"] for t in tarefas] == [1, 2]
    assert tarefas[0]["titulo"] == "Estudar MCP"
    assert tarefas[0]["concluida"] is False


def test_listar_tarefas_filtra_pendentes():
    server.adicionar_tarefa("Tarefa A")
    server.adicionar_tarefa("Tarefa B")
    server.concluir_tarefa(1)

    pendentes = server.listar_tarefas(apenas_pendentes=True)

    assert [t["id"] for t in pendentes] == [2]


def test_concluir_tarefa_inexistente_leva_erro():
    with pytest.raises(ValueError):
        server.concluir_tarefa(999)


def test_remover_tarefa():
    server.adicionar_tarefa("Tarefa temporaria")

    server.remover_tarefa(1)

    assert server.listar_tarefas() == []


def test_remover_tarefa_inexistente_leva_erro():
    with pytest.raises(ValueError):
        server.remover_tarefa(999)
