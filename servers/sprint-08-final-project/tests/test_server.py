import pytest

import server


def test_git_log_retorna_commits_recentes():
    commits = server.git_log(limite=3)

    assert len(commits) == 3
    assert all({"hash", "autor", "data", "mensagem"} <= c.keys() for c in commits)


def test_git_status_retorna_string():
    status = server.git_status()

    assert isinstance(status, str)


def test_mostrar_commit_head_contem_cabecalho_de_commit():
    saida = server.mostrar_commit("HEAD")

    assert "commit " in saida


def test_buscar_commits_por_autor_encontra_autor_conhecido():
    autor_conhecido = server.git_log(limite=1)[0]["autor"]

    encontrados = server.buscar_commits_por_autor(autor_conhecido, limite=5)

    assert len(encontrados) > 0
    assert all(autor_conhecido.lower() in c["autor"].lower() for c in encontrados)


def test_ler_readme_contem_titulo_do_projeto():
    conteudo = server.ler_readme()

    assert "Model Context Protocol" in conteudo


def test_ler_arquivo_le_arquivo_top_level():
    conteudo = server.ler_arquivo("README.md")

    assert "Sprint" in conteudo


def test_ler_arquivo_decodifica_barras_para_caminhos_aninhados():
    conteudo = server.ler_arquivo("docs%2Fsprints%2Fsprint-01.md")

    assert "Fundamentos do MCP" in conteudo


def test_ler_arquivo_bloqueia_path_traversal():
    with pytest.raises(ValueError):
        server.ler_arquivo("../../../../windows/win.ini")


def test_ler_arquivo_bloqueia_acesso_ao_git_interno():
    with pytest.raises(ValueError):
        server.ler_arquivo(".git/config")


def test_resumir_commits_recentes_prompt_inclui_mensagens():
    commits = server.git_log(limite=3)

    prompt = server.resumir_commits_recentes(limite=3)

    assert all(c["mensagem"] in prompt for c in commits)


def test_revisar_commit_prompt_inclui_o_diff():
    prompt = server.revisar_commit("HEAD")

    assert "Revise as mudancas" in prompt
    assert "commit " in prompt
