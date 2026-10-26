"""Testes da Fase 3 — `atualizar_status`.

Cobrem os casos relevantes de specs/03-atualizar-status/requisitos.md,
incluindo regressão das fases anteriores e a integração entre elas.
"""

import sqlite3

from helpdesk import banco
from servidor import atualizar_status, buscar_historico_cliente, listar_chamados


def _id_do_cliente(caminho, cliente: str) -> int:
    """Identificador do primeiro chamado de um cliente."""
    conexao = banco.conectar(caminho)
    linha = conexao.execute(
        "SELECT id FROM chamados WHERE cliente = ? ORDER BY id LIMIT 1", (cliente,)
    ).fetchone()
    conexao.close()
    return linha[0]


def _estado_completo(caminho) -> tuple:
    """Fotografia do banco, para comparar antes e depois de uma rejeição (R7)."""
    conexao = banco.conectar(caminho)
    chamados = conexao.execute("SELECT * FROM chamados ORDER BY id").fetchall()
    historico = conexao.execute("SELECT * FROM historico_status ORDER BY id").fetchall()
    conexao.close()
    return ([tuple(l) for l in chamados], [tuple(l) for l in historico])


# --- R1: atualização e persistência -----------------------------------------

def test_atualiza_status(banco_populado):
    chamado_id = _id_do_cliente(banco_populado, "Ana Souza")
    resultado = atualizar_status(chamado_id, "em_andamento")

    assert resultado["atualizado"] is True
    assert resultado["status_anterior"] == "aberto"
    assert resultado["status_novo"] == "em_andamento"
    assert "erro" not in resultado


def test_persiste_apos_reconsulta(banco_populado):
    chamado_id = _id_do_cliente(banco_populado, "Ana Souza")
    atualizar_status(chamado_id, "fechado")

    chamado = banco.buscar_chamado(chamado_id, banco_populado)
    assert chamado["status"] == "fechado"


def test_mudanca_visivel_em_listar_chamados(banco_populado):
    chamado_id = _id_do_cliente(banco_populado, "Elisa Prado")  # está "fechado"

    atualizar_status(chamado_id, "aberto")

    abertos = listar_chamados(status="aberto")["chamados"]
    assert chamado_id in [c["id"] for c in abertos]


# --- R2: histórico -----------------------------------------------------------

def test_registra_historico(banco_populado):
    chamado_id = _id_do_cliente(banco_populado, "Ana Souza")
    atualizar_status(chamado_id, "em_andamento")

    historico = banco.historico_do_chamado(chamado_id, banco_populado)

    assert len(historico) == 1
    assert historico[0]["status_anterior"] == "aberto"
    assert historico[0]["status_novo"] == "em_andamento"


def test_historico_acumula(banco_populado):
    """O ponto central do projeto: mudar o status não apaga o histórico."""
    chamado_id = _id_do_cliente(banco_populado, "Ana Souza")

    atualizar_status(chamado_id, "em_andamento")
    atualizar_status(chamado_id, "fechado")
    atualizar_status(chamado_id, "aberto")

    historico = banco.historico_do_chamado(chamado_id, banco_populado)

    assert len(historico) == 3
    assert [(h["status_anterior"], h["status_novo"]) for h in historico] == [
        ("aberto", "em_andamento"),
        ("em_andamento", "fechado"),
        ("fechado", "aberto"),
    ]


def test_historico_de_outro_chamado_nao_e_afetado(banco_populado):
    alvo = _id_do_cliente(banco_populado, "Ana Souza")
    conexao = banco.conectar(banco_populado)
    outro = conexao.execute(
        "SELECT id FROM chamados WHERE id != ? ORDER BY id LIMIT 1", (alvo,)
    ).fetchone()[0]
    conexao.close()

    atualizar_status(alvo, "fechado")

    assert banco.historico_do_chamado(outro, banco_populado) == []


# --- R3: carimbos de tempo ---------------------------------------------------

def test_atualiza_carimbo_de_tempo(banco_populado):
    chamado_id = _id_do_cliente(banco_populado, "Ana Souza")
    antes = banco.buscar_chamado(chamado_id, banco_populado)["atualizado_em"]

    atualizar_status(chamado_id, "em_andamento")
    depois = banco.buscar_chamado(chamado_id, banco_populado)["atualizado_em"]

    # O carimbo no banco é o mesmo registrado no histórico da mudança.
    assert depois == banco.historico_do_chamado(chamado_id, banco_populado)[0][
        "alterado_em"
    ]
    assert depois != antes


def test_preserva_criado_em(banco_populado):
    chamado_id = _id_do_cliente(banco_populado, "Ana Souza")
    antes = banco.buscar_chamado(chamado_id, banco_populado)["criado_em"]

    atualizar_status(chamado_id, "fechado")

    assert banco.buscar_chamado(chamado_id, banco_populado)["criado_em"] == antes


# --- R4: status inválido -----------------------------------------------------

def test_status_invalido(banco_populado):
    chamado_id = _id_do_cliente(banco_populado, "Ana Souza")
    resultado = atualizar_status(chamado_id, "encerrado")

    assert "erro" in resultado
    assert resultado["status_validos"] == list(banco.STATUS_VALIDOS)


def test_status_invalido_variacoes(banco_populado):
    chamado_id = _id_do_cliente(banco_populado, "Ana Souza")
    for invalido in ["Aberto", "ABERTO", "open", "", "em andamento"]:
        assert "erro" in atualizar_status(chamado_id, invalido), f"aceitou {invalido!r}"


# --- R5: chamado inexistente -------------------------------------------------

def test_chamado_inexistente(banco_populado):
    resultado = atualizar_status(99999, "fechado")

    assert "erro" in resultado
    assert "99999" in resultado["erro"]


def test_chamado_inexistente_nao_cria_historico_orfao(banco_populado):
    atualizar_status(99999, "fechado")

    conexao = banco.conectar(banco_populado)
    orfaos = conexao.execute(
        "SELECT COUNT(*) FROM historico_status WHERE chamado_id = 99999"
    ).fetchone()[0]
    conexao.close()

    assert orfaos == 0


# --- R6: mudança para o mesmo status ----------------------------------------

def test_status_igual_nao_registra(banco_populado):
    chamado_id = _id_do_cliente(banco_populado, "Ana Souza")  # já está "aberto"
    resultado = atualizar_status(chamado_id, "aberto")

    assert resultado["atualizado"] is False
    assert resultado["status_anterior"] == resultado["status_novo"] == "aberto"
    assert banco.historico_do_chamado(chamado_id, banco_populado) == []


def test_status_igual_nao_mexe_no_carimbo(banco_populado):
    chamado_id = _id_do_cliente(banco_populado, "Ana Souza")
    antes = banco.buscar_chamado(chamado_id, banco_populado)["atualizado_em"]

    atualizar_status(chamado_id, "aberto")

    assert banco.buscar_chamado(chamado_id, banco_populado)["atualizado_em"] == antes


# --- R7: rejeições não alteram o banco --------------------------------------

def test_rejeicoes_nao_alteram_banco(banco_populado):
    """Compara o estado completo do banco antes e depois de cada rejeição."""
    chamado_id = _id_do_cliente(banco_populado, "Ana Souza")
    antes = _estado_completo(banco_populado)

    atualizar_status(chamado_id, "encerrado")   # status inválido
    atualizar_status(99999, "fechado")          # chamado inexistente
    atualizar_status(chamado_id, "aberto")      # mesmo status

    assert _estado_completo(banco_populado) == antes


# --- R10: regressão das fases anteriores ------------------------------------

def test_regressao_listar_chamados(banco_populado):
    resultado = listar_chamados()

    assert resultado["total"] == len(banco._CHAMADOS_FICTICIOS)
    assert "erro" not in resultado


def test_regressao_buscar_historico(banco_populado):
    resultado = buscar_historico_cliente("Ana Souza")

    assert resultado["total"] == 2
    assert "erro" not in resultado


def test_regressao_apos_atualizacao(banco_populado):
    chamado_id = _id_do_cliente(banco_populado, "Ana Souza")
    total_antes = listar_chamados()["total"]

    atualizar_status(chamado_id, "fechado")

    # Atualizar status não cria nem remove chamados.
    assert listar_chamados()["total"] == total_antes
    assert buscar_historico_cliente("Ana Souza")["total"] == 2


# --- R11: integração entre a Fase 2 e a Fase 3 ------------------------------

def test_integracao_historico_visivel(banco_populado):
    """A Fase 2 lê exatamente o que a Fase 3 escreve."""
    chamado_id = _id_do_cliente(banco_populado, "Ana Souza")
    atualizar_status(chamado_id, "em_andamento")

    chamados = buscar_historico_cliente("Ana Souza")["chamados"]
    alvo = next(c for c in chamados if c["id"] == chamado_id)

    assert len(alvo["historico"]) == 1
    assert alvo["historico"][0]["status_novo"] == "em_andamento"
    assert alvo["status"] == "em_andamento"


def test_integracao_resumo_reflete_atualizacao(banco_populado):
    chamado_id = _id_do_cliente(banco_populado, "Bruno Lima")  # está "aberto"
    antes = buscar_historico_cliente("Bruno Lima")["resumo"]["por_status"]

    atualizar_status(chamado_id, "em_andamento")

    depois = buscar_historico_cliente("Bruno Lima")["resumo"]["por_status"]
    assert depois["aberto"] == antes["aberto"] - 1
    assert depois["em_andamento"] == antes["em_andamento"] + 1
