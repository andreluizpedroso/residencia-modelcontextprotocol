import pytest

import server


def test_listar_notas_retorna_id_e_titulo():
    notas = server.listar_notas()

    ids = [n["id"] for n in notas]
    assert "mcp-intro" in ids
    assert all("titulo" in n for n in notas)


def test_ler_nota_retorna_conteudo():
    conteudo = server.ler_nota("json-rpc")

    assert "JSON-RPC" in conteudo


def test_ler_nota_inexistente_leva_erro():
    with pytest.raises(ValueError):
        server.ler_nota("nao-existe")


def test_resumir_nota_inclui_titulo_e_conteudo():
    prompt = server.resumir_nota("uv-cheatsheet")

    assert "uv - comandos essenciais" in prompt
    assert "uv init" in prompt


def test_resumir_nota_inexistente_leva_erro():
    with pytest.raises(ValueError):
        server.resumir_nota("nao-existe")


def test_revisar_nota_usa_foco_informado():
    mensagens = server.revisar_nota("mcp-intro", foco="precisao tecnica")

    assert len(mensagens) == 1
    assert "precisao tecnica" in mensagens[0].content.text
