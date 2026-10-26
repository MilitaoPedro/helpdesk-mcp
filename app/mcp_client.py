"""Cliente MCP usado pelo app Streamlit.

Conecta ao servidor `servidor.py` via stdio e expõe as três ferramentas como
métodos Python. Todo o acesso do app aos dados passa por aqui: o app **não**
abre o SQLite diretamente.

O cliente é assíncrono (`fastmcp.Client`), enquanto o Streamlit executa o
script de cima para baixo em contexto síncrono. Por isso cada método cria seu
próprio event loop e abre uma conexão curta com o servidor.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

RAIZ = Path(__file__).resolve().parent.parent
SERVIDOR = RAIZ / "servidor.py"


class ErroMCP(RuntimeError):
    """Falha ao conversar com o servidor MCP."""


def _executar(nome_ferramenta: str, argumentos: dict) -> dict:
    """Chama uma ferramenta do servidor e devolve o resultado como dicionário.

    Abre uma conexão nova a cada chamada. É mais simples do que manter uma
    sessão viva entre reruns do Streamlit, que reexecuta o script inteiro a
    cada interação, e o custo de iniciar o processo é irrelevante para um
    protótipo de uso local.
    """

    async def chamar() -> dict:
        transporte = PythonStdioTransport(script_path=str(SERVIDOR), cwd=str(RAIZ))
        async with Client(transporte) as cliente:
            resultado = await cliente.call_tool(nome_ferramenta, argumentos)
            return resultado.data

    try:
        return asyncio.run(chamar())
    except FileNotFoundError as erro:
        raise ErroMCP(
            f"Não foi possível iniciar o servidor MCP em {SERVIDOR}. "
            "Verifique se o arquivo existe."
        ) from erro
    except Exception as erro:  # noqa: BLE001 — vira mensagem na interface
        raise ErroMCP(f"Falha ao chamar {nome_ferramenta!r}: {erro}") from erro


def listar_chamados(status: str | None = None) -> dict:
    """Lista os chamados, opcionalmente filtrando por status."""
    argumentos = {} if status is None else {"status": status}
    return _executar("listar_chamados", argumentos)


def buscar_historico_cliente(cliente: str) -> dict:
    """Retorna os chamados de um cliente e o histórico de cada um."""
    return _executar("buscar_historico_cliente", {"cliente": cliente})


def atualizar_status(chamado_id: int, novo_status: str) -> dict:
    """Altera o status de um chamado."""
    return _executar(
        "atualizar_status", {"chamado_id": chamado_id, "novo_status": novo_status}
    )
