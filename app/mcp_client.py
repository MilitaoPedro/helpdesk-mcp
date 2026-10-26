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
import os
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

class ErroMCP(RuntimeError):
    """Falha ao conversar com o servidor MCP."""


# O app pode ser executado em dois arranjos:
#
#   1. dentro do repositório, com o servidor na raiz do projeto:
#        helpdesk-mcp/app/mcp_client.py  ->  helpdesk-mcp/servidor.py
#
#   2. empacotado em duas pastas lado a lado, para entrega:
#        app-streamlit/app/mcp_client.py ->  servidor-mcp/servidor.py
#
# Em vez de fixar um caminho, procuramos o servidor nos locais conhecidos.
AQUI = Path(__file__).resolve().parent
PROJETO = AQUI.parent

NOME_PASTA_SERVIDOR = "servidor-mcp"

# Permite apontar o servidor manualmente quando ele estiver em outro lugar.
VARIAVEL_AMBIENTE = "HELPDESK_SERVIDOR"


def _candidatos() -> list[Path]:
    """Locais onde o servidor pode estar, em ordem de preferência."""
    candidatos: list[Path] = []

    if caminho := os.environ.get(VARIAVEL_AMBIENTE):
        candidatos.append(Path(caminho).expanduser())

    # Arranjo de entrega: pasta irmã.
    candidatos.append(PROJETO.parent / NOME_PASTA_SERVIDOR / "servidor.py")

    # Arranjo do repositório: servidor na raiz do projeto.
    candidatos.append(PROJETO / "servidor.py")

    return candidatos


def _localizar_servidor() -> Path:
    """Primeiro candidato que existe. Levanta ErroMCP se nenhum existir."""
    candidatos = _candidatos()
    for candidato in candidatos:
        if candidato.is_file():
            return candidato

    procurados = "\n".join(f"  - {c}" for c in candidatos)
    raise ErroMCP(
        "Servidor MCP não encontrado. Procurei em:\n"
        f"{procurados}\n"
        f"Defina {VARIAVEL_AMBIENTE} com o caminho do servidor.py "
        "se ele estiver em outro lugar."
    )


def _executar(nome_ferramenta: str, argumentos: dict) -> dict:
    """Chama uma ferramenta do servidor e devolve o resultado como dicionário.

    Abre uma conexão nova a cada chamada. É mais simples do que manter uma
    sessão viva entre reruns do Streamlit, que reexecuta o script inteiro a
    cada interação, e o custo de iniciar o processo é irrelevante para um
    protótipo de uso local.
    """

    servidor = _localizar_servidor()

    async def chamar() -> dict:
        transporte = PythonStdioTransport(
            script_path=str(servidor), cwd=str(servidor.parent)
        )
        async with Client(transporte) as cliente:
            resultado = await cliente.call_tool(nome_ferramenta, argumentos)
            return resultado.data

    try:
        return asyncio.run(chamar())
    except FileNotFoundError as erro:
        raise ErroMCP(
            f"Não foi possível iniciar o servidor MCP em {servidor}. "
            "Confira se o arquivo existe e se o ambiente virtual está ativo."
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
