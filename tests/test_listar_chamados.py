"""Testes da Fase 1 — `listar_chamados`.

Cobrem os casos relevantes de specs/01-listar-chamados/requisitos.md.
"""

import sqlite3

from helpdesk import banco
from servidor import listar_chamados


# --- R1: listar todos -------------------------------------------------------

def test_listar_todos(banco_populado):
    resultado = listar_chamados()

    assert resultado["total"] == len(banco._CHAMADOS_FICTICIOS)
    assert len(resultado["chamados"]) == resultado["total"]
    assert "erro" not in resultado


def test_campos_de_cada_chamado(banco_populado):
    chamado = listar_chamados()["chamados"][0]

    assert set(chamado) == {
        "id",
        "cliente",
        "descricao",
        "status",
        "criado_em",
        "atualizado_em",
    }


def test_ordenado_do_mais_recente_para_o_mais_antigo(banco_populado):
    datas = [c["criado_em"] for c in listar_chamados()["chamados"]]
    assert datas == sorted(datas, reverse=True)


# --- R2: filtro por status --------------------------------------------------

def test_filtrar_por_status(banco_populado):
    for status in banco.STATUS_VALIDOS:
        resultado = listar_chamados(status=status)
        assert resultado["total"] > 0, f"o seed deveria ter chamados {status!r}"
        assert all(c["status"] == status for c in resultado["chamados"])


def test_soma_dos_filtros_igual_ao_total(banco_populado):
    por_status = sum(
        listar_chamados(status=s)["total"] for s in banco.STATUS_VALIDOS
    )
    assert por_status == listar_chamados()["total"]


# --- R3: filtro válido sem resultados --------------------------------------

def test_filtro_sem_resultados(banco_temporario, monkeypatch):
    # Banco com um único chamado aberto: filtrar por "fechado" não acha nada.
    monkeypatch.setattr(
        banco, "_CHAMADOS_FICTICIOS", [("Cliente X", "Problema Y", "aberto", 0)]
    )
    banco.inicializar(banco_temporario).close()

    resultado = listar_chamados(status="fechado")

    assert resultado["total"] == 0
    assert resultado["chamados"] == []
    assert "erro" not in resultado  # lista vazia não é erro


# --- R4: status inválido ----------------------------------------------------

def test_status_invalido(banco_populado):
    resultado = listar_chamados(status="abertos")

    assert "erro" in resultado
    assert resultado["status_validos"] == list(banco.STATUS_VALIDOS)
    assert "chamados" not in resultado


def test_status_invalido_variacoes(banco_populado):
    for invalido in ["Aberto", "ABERTO", "open", "", "em andamento"]:
        assert "erro" in listar_chamados(status=invalido), f"aceitou {invalido!r}"


# --- R5: criação e povoamento automáticos ----------------------------------

def test_cria_banco_quando_ausente(banco_temporario):
    assert not banco_temporario.exists()

    conexao = banco.inicializar(banco_temporario)
    total = conexao.execute("SELECT COUNT(*) FROM chamados").fetchone()[0]
    conexao.close()

    assert banco_temporario.exists()
    assert total == len(banco._CHAMADOS_FICTICIOS)


def test_cria_as_duas_tabelas(banco_populado):
    conexao = banco.conectar(banco_populado)
    tabelas = {
        linha[0]
        for linha in conexao.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    conexao.close()

    assert {"chamados", "historico_status"} <= tabelas


# --- R6: inicialização não destrutiva --------------------------------------

def test_nao_apaga_dados_existentes(banco_populado):
    conexao = banco.conectar(banco_populado)
    conexao.execute(
        "INSERT INTO chamados (cliente, descricao, status, criado_em, atualizado_em)"
        " VALUES ('Cliente Novo', 'Chamado inserido à mão', 'aberto', '2026-01-01', '2026-01-01')"
    )
    conexao.commit()
    conexao.close()

    # Reexecutar a inicialização não pode apagar o registro inserido...
    banco.inicializar(banco_populado).close()
    assert listar_chamados()["total"] == len(banco._CHAMADOS_FICTICIOS) + 1


def test_inicializacao_nao_duplica(banco_populado):
    # ...nem duplicar os dados fictícios.
    for _ in range(3):
        banco.inicializar(banco_populado).close()

    assert listar_chamados()["total"] == len(banco._CHAMADOS_FICTICIOS)
