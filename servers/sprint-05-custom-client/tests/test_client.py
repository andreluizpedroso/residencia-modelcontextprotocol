import asyncio

import client

SPRINT_02_SERVER = ["uv", "run", "--directory", "../sprint-02-tools-server", "server.py"]


def test_parse_value_coerces_json_types():
    assert client.parse_value("42") == 42
    assert client.parse_value("true") is True
    assert client.parse_value("3.5") == 3.5
    assert client.parse_value("Testar algo") == "Testar algo"


def test_parse_kv_pairs():
    assert client.parse_kv_pairs(["a=1", "b=dois"]) == {"a": "1", "b": "dois"}


def test_run_list_contra_server_de_tarefas(capsys):
    exit_code = asyncio.run(
        client.run(SPRINT_02_SERVER[0], SPRINT_02_SERVER[1:], "list", [])
    )

    saida = capsys.readouterr().out
    assert exit_code == 0
    assert "adicionar_tarefa" in saida


def test_run_call_com_erro_retorna_exit_code_1():
    exit_code = asyncio.run(
        client.run(
            SPRINT_02_SERVER[0],
            SPRINT_02_SERVER[1:],
            "call",
            ["concluir_tarefa", "id=999"],
        )
    )

    assert exit_code == 1
