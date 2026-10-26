"""Validação ponta a ponta: chama o servidor pelo protocolo MCP.

Diferente dos testes unitários, este script conecta ao servidor via stdio como
um cliente MCP real faria, exercitando o nome exposto da ferramenta, o esquema
dos parâmetros e a serialização da resposta — coisas que só existem no
protocolo e que uma chamada direta de função Python não verifica.

Uso:
    python scripts/demo_mcp.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

RAIZ = Path(__file__).resolve().parent.parent
SERVIDOR = RAIZ / "servidor.py"

# Cores simples para leitura; desativadas quando a saída não é um terminal.
COR = sys.stdout.isatty()


def titulo(texto: str) -> None:
    print(f"\n{'=' * 62}\n{texto}\n{'=' * 62}")


async def main() -> int:
    falhas: list[str] = []

    transporte = PythonStdioTransport(script_path=str(SERVIDOR), cwd=str(RAIZ))

    async with Client(transporte) as cliente:
        # 1. A ferramenta está exposta?
        titulo("1. Ferramentas expostas pelo servidor")
        ferramentas = await cliente.list_tools()
        nomes = [f.name for f in ferramentas]
        print(f"  {nomes}")
        if "listar_chamados" not in nomes:
            falhas.append("listar_chamados não está exposta")

        # 2. Sem filtro.
        titulo("2. listar_chamados() — sem filtro")
        r = (await cliente.call_tool("listar_chamados", {})).data
        print(f"  total = {r.get('total')}")
        for c in r.get("chamados", [])[:3]:
            print(f"    #{c['id']} {c['cliente']:<14} {c['status']}")
        if r.get("total", 0) == 0:
            falhas.append("sem filtro não retornou chamados")

        # 3. Cada status válido.
        titulo("3. listar_chamados(status=...) — cada status válido")
        for status in ("aberto", "em_andamento", "fechado"):
            r = (await cliente.call_tool("listar_chamados", {"status": status})).data
            total = r.get("total")
            coerente = all(c["status"] == status for c in r.get("chamados", []))
            print(f"  {status:<14} total = {total}  (todos com esse status: {coerente})")
            if not coerente:
                falhas.append(f"filtro {status!r} devolveu chamados de outro status")

        # 4. Status inválido: precisa virar erro, sem derrubar o servidor.
        titulo("4. listar_chamados(status='abertos') — status inválido")
        r = (await cliente.call_tool("listar_chamados", {"status": "abertos"})).data
        print(f"  erro: {r.get('erro')}")
        print(f"  status_validos: {r.get('status_validos')}")
        if "erro" not in r:
            falhas.append("status inválido não retornou erro")

        # 5. O servidor sobreviveu ao erro?
        titulo("5. Servidor continua respondendo após o erro")
        r = (await cliente.call_tool("listar_chamados", {})).data
        print(f"  total = {r.get('total')}")
        if "total" not in r:
            falhas.append("servidor não respondeu após status inválido")

    titulo("Resultado")
    if falhas:
        for f in falhas:
            print(f"  ✗ {f}")
        return 1
    print("  Todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
