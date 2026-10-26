"""Testes da Parte 2 — interpretação de comandos e integração com o servidor.

A interpretação de comandos é testada isoladamente (sem Streamlit) e a
integração é testada chamando as ferramentas pelo protocolo MCP, que é o que
o app faz em execução.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import comandos as cmds  # noqa: E402
import mcp_client  # noqa: E402


# --- localização do servidor -------------------------------------------------

def test_localiza_servidor_no_arranjo_atual():
    """Encontra o servidor em qualquer um dos dois arranjos.

    Este teste roda tanto no repositório (servidor na raiz do projeto) quanto
    no pacote de entrega (servidor na pasta irmã), então não pode fixar um
    caminho: verifica que o servidor achado é um dos candidatos e que o
    arquivo existe de fato.
    """
    servidor = mcp_client._localizar_servidor()

    assert servidor.is_file()
    assert servidor.name == "servidor.py"
    assert servidor in mcp_client._candidatos()


def test_candidatos_incluem_os_dois_arranjos(monkeypatch):
    """Os dois arranjos conhecidos estão entre os candidatos."""
    monkeypatch.setenv(mcp_client.VARIAVEL_AMBIENTE, "/tmp/inexistente/servidor.py")
    candidatos = mcp_client._candidatos()

    # Arranjo do repositório: servidor na raiz do projeto.
    assert mcp_client.PROJETO / "servidor.py" in candidatos

    # Arranjo da entrega: servidor na pasta irmã.
    esperado = mcp_client.PROJETO.parent / mcp_client.NOME_PASTA_SERVIDOR / "servidor.py"
    assert esperado in candidatos


def test_variavel_de_ambiente_tem_preferencia(monkeypatch, tmp_path):
    """HELPDESK_SERVIDOR permite apontar o servidor para outro lugar."""
    falso = tmp_path / "servidor.py"
    falso.write_text("# servidor de mentira\n")
    monkeypatch.setenv(mcp_client.VARIAVEL_AMBIENTE, str(falso))

    assert mcp_client._localizar_servidor() == falso


def test_erro_quando_servidor_nao_existe(monkeypatch, tmp_path):
    """Sem nenhum candidato válido, o erro explica onde se procurou."""
    monkeypatch.setenv(mcp_client.VARIAVEL_AMBIENTE, str(tmp_path / "nao-existe.py"))
    monkeypatch.setattr(mcp_client, "PROJETO", tmp_path)

    with pytest.raises(mcp_client.ErroMCP) as erro:
        mcp_client._localizar_servidor()

    assert "não encontrado" in str(erro.value)
    assert mcp_client.VARIAVEL_AMBIENTE in str(erro.value)


# --- interpretação: listar ---------------------------------------------------

@pytest.mark.parametrize(
    "texto, status",
    [
        ("listar todos", None),
        ("lista todos", None),
        ("mostrar todos", None),
        ("listar", None),
        ("listar abertos", "aberto"),
        ("listar aberto", "aberto"),
        ("listar os chamados abertos", "aberto"),
        ("listar fechados", "fechado"),
        ("listar encerrados", "fechado"),  # sinônimo
        ("listar em andamento", "em_andamento"),
        ("mostrar chamados em andamento", "em_andamento"),
        ("listar com status aberto", "aberto"),
    ],
)
def test_interpretar_listar(texto, status):
    comando = cmds.interpretar(texto)

    assert comando.ferramenta == "listar_chamados"
    if status is None:
        assert "status" not in comando.argumentos
    else:
        assert comando.argumentos["status"] == status


# --- interpretação: histórico ------------------------------------------------

@pytest.mark.parametrize(
    "texto, cliente",
    [
        ("historico do cliente Ana Souza", "Ana Souza"),
        ("histórico do cliente Ana Souza", "Ana Souza"),
        ("historico da ana souza", "ana souza"),
        ("chamados do cliente Bruno Lima", "Bruno Lima"),
    ],
)
def test_interpretar_historico_por_nome(texto, cliente):
    comando = cmds.interpretar(texto)

    assert comando.ferramenta == "buscar_historico_cliente"
    assert comando.argumentos["cliente"] == cliente
    assert comando.resolver_cliente_por_chamado is False


def test_interpretar_historico_preserva_grafia_do_nome():
    # O nome deve sair como o atendente digitou, e não normalizado.
    assert cmds.interpretar("historico do cliente Ana Souza").argumentos["cliente"] == (
        "Ana Souza"
    )
    assert cmds.interpretar("Histórico do Cliente Bruno Lima").argumentos[
        "cliente"
    ] == "Bruno Lima"


def test_interpretar_historico_com_chamados_no_plural():
    """Regressão: 'chamados' contém 'dos', que era casado como preposição."""
    assert cmds.interpretar("chamados da ana souza").argumentos["cliente"] == (
        "ana souza"
    )
    assert cmds.interpretar("chamados do cliente Bruno Lima").argumentos[
        "cliente"
    ] == "Bruno Lima"


def test_interpretar_historico_por_numero_de_chamado():
    """O exemplo dos slides: 'histórico do cliente 2'."""
    comando = cmds.interpretar("historico do cliente 2")

    assert comando.ferramenta == "buscar_historico_cliente"
    assert comando.argumentos["cliente"] == "2"
    assert comando.resolver_cliente_por_chamado is True


# --- interpretação: atualizar -------------------------------------------------

@pytest.mark.parametrize(
    "texto, chamado_id, status",
    [
        ("alterar chamado 3 para fechado", 3, "fechado"),
        ("alterar o chamado 3 para fechado", 3, "fechado"),
        ("mudar chamado 12 para em andamento", 12, "em_andamento"),
        ("atualizar chamado 7 para aberto", 7, "aberto"),
        ("alterar chamado 1 para encerrado", 1, "fechado"),  # sinônimo
        ("alterar chamado 5 para em_andamento", 5, "em_andamento"),
    ],
)
def test_interpretar_atualizar(texto, chamado_id, status):
    comando = cmds.interpretar(texto)

    assert comando.ferramenta == "atualizar_status"
    assert comando.argumentos == {"chamado_id": chamado_id, "novo_status": status}


# --- interpretação: ajuda e rejeições -----------------------------------------

def test_interpretar_ajuda():
    assert cmds.interpretar("ajuda").ferramenta == "ajuda"
    assert cmds.interpretar("help").ferramenta == "ajuda"


@pytest.mark.parametrize(
    "texto",
    ["", "   ", "bom dia", "tudo bem?", "listar roxo", "qualquer coisa"],
)
def test_comandos_invalidos(texto):
    with pytest.raises(cmds.ComandoInvalido):
        cmds.interpretar(texto)


def test_status_invalido_no_comando_de_alteracao():
    with pytest.raises(cmds.ComandoInvalido, match="[Ss]tatus"):
        cmds.interpretar("alterar chamado 1 para roxo")


def test_status_invalido_na_listagem_sugere_os_validos():
    with pytest.raises(cmds.ComandoInvalido) as erro:
        cmds.interpretar("listar roxo")
    assert "aberto" in str(erro.value)


# --- normalização -------------------------------------------------------------

def test_normalizacao_ignora_acentos_e_caixa():
    assert cmds.interpretar("LISTAR ABERTOS").argumentos["status"] == "aberto"
    assert cmds.interpretar("Histórico do Cliente Ana Souza").ferramenta == (
        "buscar_historico_cliente"
    )


def test_normalizacao_ignora_espacos_extras():
    assert cmds.interpretar("  listar    abertos  ").argumentos["status"] == "aberto"
