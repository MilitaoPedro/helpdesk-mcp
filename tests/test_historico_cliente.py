"""Testes da Fase 2 — `buscar_historico_cliente`.

Cobrem os casos relevantes de specs/02-historico-cliente/requisitos.md,
incluindo a regressão da Fase 1.
"""

from helpdesk import banco
from servidor import buscar_historico_cliente, listar_chamados


# --- R1: chamados do cliente -------------------------------------------------

def test_retorna_chamados_do_cliente(banco_populado):
    resultado = buscar_historico_cliente("Ana Souza")

    # O seed tem dois chamados para a Ana.
    assert resultado["total"] == 2
    assert all(c["cliente"] == "Ana Souza" for c in resultado["chamados"])


def test_nao_inclui_chamados_de_outros_clientes(banco_populado):
    resultado = buscar_historico_cliente("Bruno Lima")

    assert resultado["total"] == 1
    assert resultado["chamados"][0]["cliente"] == "Bruno Lima"


def test_ordenado_do_mais_recente(banco_populado):
    chamados = buscar_historico_cliente("Ana Souza")["chamados"]
    datas = [c["criado_em"] for c in chamados]
    assert datas == sorted(datas, reverse=True)


# --- R2: histórico -----------------------------------------------------------

def test_historico_presente_em_cada_chamado(banco_populado):
    for chamado in buscar_historico_cliente("Ana Souza")["chamados"]:
        assert "historico" in chamado
        assert isinstance(chamado["historico"], list)


def test_historico_vazio_quando_nao_ha_mudancas(banco_populado):
    # O seed não registra mudanças de status: a lista deve vir vazia.
    for chamado in buscar_historico_cliente("Ana Souza")["chamados"]:
        assert chamado["historico"] == []


def test_historico_com_mudanca_registrada(banco_populado):
    """Exercita a leitura do histórico, e não só o caminho vazio.

    Sem este teste, a leitura do histórico passaria a Fase 2 sem nunca ter
    devolvido um registro de verdade.
    """
    conexao = banco.conectar(banco_populado)
    chamado_id = conexao.execute(
        "SELECT id FROM chamados WHERE cliente = 'Ana Souza' ORDER BY id LIMIT 1"
    ).fetchone()[0]
    conexao.execute(
        """
        INSERT INTO historico_status
            (chamado_id, status_anterior, status_novo, alterado_em)
        VALUES (?, 'aberto', 'em_andamento', '2026-02-01T10:00:00+00:00')
        """,
        (chamado_id,),
    )
    conexao.commit()
    conexao.close()

    chamados = buscar_historico_cliente("Ana Souza")["chamados"]
    alvo = next(c for c in chamados if c["id"] == chamado_id)

    assert len(alvo["historico"]) == 1
    assert alvo["historico"][0]["status_anterior"] == "aberto"
    assert alvo["historico"][0]["status_novo"] == "em_andamento"


def test_historico_em_ordem_cronologica(banco_populado):
    conexao = banco.conectar(banco_populado)
    chamado_id = conexao.execute(
        "SELECT id FROM chamados ORDER BY id LIMIT 1"
    ).fetchone()[0]
    # Inseridas fora de ordem de propósito.
    conexao.executemany(
        """
        INSERT INTO historico_status
            (chamado_id, status_anterior, status_novo, alterado_em)
        VALUES (?, ?, ?, ?)
        """,
        [
            (chamado_id, "em_andamento", "fechado", "2026-03-01T10:00:00+00:00"),
            (chamado_id, "aberto", "em_andamento", "2026-02-01T10:00:00+00:00"),
        ],
    )
    conexao.commit()
    conexao.close()

    historico = banco.historico_do_chamado(chamado_id, banco_populado)
    datas = [h["alterado_em"] for h in historico]

    assert datas == sorted(datas)
    assert datas[0].startswith("2026-02-01")


# --- R3: cliente sem chamados ------------------------------------------------

def test_cliente_sem_chamados(banco_populado):
    resultado = buscar_historico_cliente("Cliente Que Nao Existe")

    assert resultado["total"] == 0
    assert resultado["chamados"] == []
    assert "erro" not in resultado


def test_cliente_com_nome_parecido_nao_e_encontrado(banco_populado):
    # Correspondência é exata: "Ana" não deve trazer os chamados de "Ana Souza".
    assert buscar_historico_cliente("Ana")["total"] == 0


# --- R4: nome vazio ----------------------------------------------------------

def test_nome_vazio(banco_populado):
    for vazio in ["", "   ", "\t"]:
        resultado = buscar_historico_cliente(vazio)
        assert "erro" in resultado, f"aceitou {vazio!r}"


def test_erro_nao_derruba_o_servidor(banco_populado):
    buscar_historico_cliente("")
    # Se a chamada acima lançasse exceção, esta linha não seria alcançada.
    assert buscar_historico_cliente("Ana Souza")["total"] == 2


# --- R5: correspondência -----------------------------------------------------

def test_nome_com_maiusculas_diferentes(banco_populado):
    for variante in ["ana souza", "ANA SOUZA", "Ana souza"]:
        assert buscar_historico_cliente(variante)["total"] == 2, variante


def test_nome_com_espacos_nas_pontas(banco_populado):
    assert buscar_historico_cliente("  Ana Souza  ")["total"] == 2


# --- R6: resumo --------------------------------------------------------------

def test_resumo_por_status(banco_populado):
    resultado = buscar_historico_cliente("Ana Souza")

    assert resultado["resumo"]["por_status"]["aberto"] == 1
    assert resultado["resumo"]["por_status"]["em_andamento"] == 1
    assert resultado["resumo"]["por_status"]["fechado"] == 0


def test_resumo_bate_com_total(banco_populado):
    for cliente in ["Ana Souza", "Bruno Lima", "Carla Mendes"]:
        resultado = buscar_historico_cliente(cliente)
        soma = sum(resultado["resumo"]["por_status"].values())
        assert soma == resultado["total"], cliente


def test_resumo_traz_todos_os_status_mesmo_zerados(banco_populado):
    por_status = buscar_historico_cliente("Bruno Lima")["resumo"]["por_status"]
    assert set(por_status) == set(banco.STATUS_VALIDOS)


# --- R9: regressão da Fase 1 -------------------------------------------------

def test_regressao_listar_chamados(banco_populado):
    resultado = listar_chamados()

    assert resultado["total"] == len(banco._CHAMADOS_FICTICIOS)
    assert "erro" not in resultado


def test_regressao_listar_chamados_filtro(banco_populado):
    resultado = listar_chamados(status="aberto")

    assert resultado["total"] == 2
    assert all(c["status"] == "aberto" for c in resultado["chamados"])


def test_regressao_listar_chamados_status_invalido(banco_populado):
    assert "erro" in listar_chamados(status="abertos")


def test_listar_chamados_nao_traz_historico(banco_populado):
    # O histórico é específico da ferramenta da Fase 2; listar_chamados
    # mantém o formato definido na Fase 1.
    chamado = listar_chamados()["chamados"][0]
    assert "historico" not in chamado
