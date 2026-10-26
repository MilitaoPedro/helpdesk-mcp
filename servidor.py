"""Servidor MCP do helpdesk.

Expõe as operações de consulta e atualização de chamados como ferramentas MCP,
para que agentes de IA possam executá-las.

Execução (transporte stdio, o padrão):
    python servidor.py

Atenção: em stdio, nada além do protocolo pode ser escrito em stdout. Use
stderr ou logging para depuração — um print() em stdout corrompe a comunicação.
"""

from __future__ import annotations

from fastmcp import FastMCP

from helpdesk import banco

mcp = FastMCP("Helpdesk")


@mcp.tool()
def listar_chamados(status: str | None = None) -> dict:
    """Lista os chamados de suporte, opcionalmente filtrando por status.

    Args:
        status: Filtra pelo status do chamado. Valores aceitos: "aberto",
            "em_andamento" ou "fechado". Se omitido, retorna todos os chamados.

    Returns:
        Um objeto com "total" (quantidade) e "chamados" (lista, do mais recente
        para o mais antigo). Se o status informado for inválido, retorna "erro"
        e "status_validos" em vez da lista.
    """
    if status is not None and status not in banco.STATUS_VALIDOS:
        # Erro de entrada é devolvido como resultado, não como exceção: um
        # agente pode enviar qualquer texto, e uma exceção derrubaria o servidor.
        return {
            "erro": f"Status inválido: {status!r}.",
            "status_validos": list(banco.STATUS_VALIDOS),
        }

    chamados = banco.listar(status)
    return {
        "total": len(chamados),
        "chamados": chamados,
    }


@mcp.tool()
def buscar_historico_cliente(cliente: str) -> dict:
    """Retorna os chamados de um cliente e o histórico de status de cada um.

    Use esta ferramenta quando a pergunta for sobre um cliente específico
    ("quantos chamados abertos o cliente X tem?", "qual o histórico do cliente
    X?"). Para listar chamados por status, sem filtrar por cliente, use
    `listar_chamados`.

    Args:
        cliente: Nome do cliente. A busca ignora maiúsculas/minúsculas e
            espaços nas pontas, mas não encontra nomes parciais.

    Returns:
        Um objeto com "cliente", "total", "resumo" (contagem por status) e
        "chamados" — cada chamado incluindo seu campo "historico". Cliente sem
        chamados retorna "total" igual a zero, sem erro. Nome vazio retorna
        "erro".
    """
    if not cliente or not cliente.strip():
        # Mesmo padrão da Fase 1: erro de entrada é resultado, não exceção.
        return {"erro": "O nome do cliente não pode ser vazio."}

    chamados = banco.listar_por_cliente(cliente)

    # Anexa o histórico de cada chamado (R2).
    for chamado in chamados:
        chamado["historico"] = banco.historico_do_chamado(chamado["id"])

    # O resumo deriva da mesma lista retornada, para não divergir dela (R6).
    por_status = {status: 0 for status in banco.STATUS_VALIDOS}
    for chamado in chamados:
        por_status[chamado["status"]] = por_status.get(chamado["status"], 0) + 1

    return {
        "cliente": cliente.strip(),
        "total": len(chamados),
        "resumo": {"por_status": por_status},
        "chamados": chamados,
    }


@mcp.tool()
def atualizar_status(chamado_id: int, novo_status: str) -> dict:
    """Altera o status de um chamado e registra a mudança no histórico.

    Atenção: esta é a única ferramenta que ALTERA dados. As demais apenas
    consultam.

    Args:
        chamado_id: Identificador do chamado a alterar.
        novo_status: O novo status. Valores aceitos: "aberto", "em_andamento"
            ou "fechado".

    Returns:
        Em caso de mudança: "atualizado" (true), o chamado, o status anterior e
        o novo. Se o chamado já estava nesse status, retorna "atualizado" igual
        a false, sem registrar nada. Status inválido ou chamado inexistente
        retornam "erro".
    """
    if novo_status not in banco.STATUS_VALIDOS:
        return {
            "erro": f"Status inválido: {novo_status!r}.",
            "status_validos": list(banco.STATUS_VALIDOS),
        }

    resultado = banco.atualizar_status(chamado_id, novo_status)

    if resultado["resultado"] == "nao_encontrado":
        return {"erro": f"Chamado {chamado_id} não encontrado."}

    if resultado["resultado"] == "sem_mudanca":
        return {
            "atualizado": False,
            "chamado_id": chamado_id,
            "status_anterior": resultado["status_anterior"],
            "status_novo": resultado["status_novo"],
            "mensagem": (
                f"O chamado {chamado_id} já estava com o status "
                f"{novo_status!r}; nada foi alterado."
            ),
        }

    return {
        "atualizado": True,
        "chamado_id": chamado_id,
        "status_anterior": resultado["status_anterior"],
        "status_novo": resultado["status_novo"],
        "mensagem": (
            f"Chamado {chamado_id}: status alterado de "
            f"{resultado['status_anterior']!r} para {novo_status!r}."
        ),
    }


if __name__ == "__main__":
    # Garante que o banco existe e está populado antes de aceitar chamadas.
    banco.inicializar().close()
    mcp.run()
