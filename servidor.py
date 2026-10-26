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


if __name__ == "__main__":
    # Garante que o banco existe e está populado antes de aceitar chamadas.
    banco.inicializar().close()
    mcp.run()
