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
        esperadas = ("listar_chamados", "buscar_historico_cliente", "atualizar_status")
        for esperada in esperadas:
            if esperada not in nomes:
                falhas.append(f"{esperada} não está exposta")

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

        # 6. Cliente com vários chamados, com histórico.
        titulo("6. buscar_historico_cliente('Ana Souza')")
        r = (await cliente.call_tool(
            "buscar_historico_cliente", {"cliente": "Ana Souza"}
        )).data
        print(f"  total = {r.get('total')}  resumo = {r.get('resumo', {}).get('por_status')}")
        for c in r.get("chamados", []):
            print(f"    #{c['id']} {c['status']:<13} histórico: {len(c['historico'])} evento(s)")
        if r.get("total", 0) == 0:
            falhas.append("cliente com chamados retornou vazio")
        if any("historico" not in c for c in r.get("chamados", [])):
            falhas.append("chamado sem o campo historico")

        # 7. Cliente inexistente: vazio, e não erro.
        titulo("7. buscar_historico_cliente('Cliente Inexistente')")
        r = (await cliente.call_tool(
            "buscar_historico_cliente", {"cliente": "Cliente Inexistente"}
        )).data
        print(f"  total = {r.get('total')}  erro = {r.get('erro')}")
        if r.get("total") != 0 or "erro" in r:
            falhas.append("cliente inexistente deveria retornar vazio sem erro")

        # 8. Nome vazio: erro.
        titulo("8. buscar_historico_cliente('') — nome vazio")
        r = (await cliente.call_tool("buscar_historico_cliente", {"cliente": ""})).data
        print(f"  erro = {r.get('erro')}")
        if "erro" not in r:
            falhas.append("nome vazio não retornou erro")

        # 9. Regressão: a Fase 1 continua funcionando via protocolo.
        titulo("9. Regressão — listar_chamados continua respondendo")
        r = (await cliente.call_tool("listar_chamados", {"status": "fechado"})).data
        print(f"  fechados = {r.get('total')}")
        if "total" not in r:
            falhas.append("listar_chamados não respondeu (regressão)")

        # ------------------------------------------------------------------
        # Fase 3 — escrita: atualizar_status
        # ------------------------------------------------------------------

        # 10. Erros primeiro, sem tocar nos dados: status inválido e id inexistente.
        titulo("10. atualizar_status — entradas inválidas")
        r = (await cliente.call_tool(
            "atualizar_status", {"chamado_id": 1, "novo_status": "encerrado"}
        )).data
        print(f"  status inválido  -> erro: {r.get('erro')}")
        if "erro" not in r:
            falhas.append("status inválido não retornou erro")

        r = (await cliente.call_tool(
            "atualizar_status", {"chamado_id": 999999, "novo_status": "fechado"}
        )).data
        print(f"  chamado inexistente -> erro: {r.get('erro')}")
        if "erro" not in r:
            falhas.append("chamado inexistente não retornou erro")

        # 11. Mudança real, em um chamado aberto, com histórico limpo.
        titulo("11. atualizar_status — mudança de status")
        abertos = (await cliente.call_tool(
            "listar_chamados", {"status": "aberto"}
        )).data["chamados"]
        if abertos:
            alvo = abertos[0]["id"]
            r = (await cliente.call_tool(
                "atualizar_status", {"chamado_id": alvo, "novo_status": "em_andamento"}
            )).data
            print(f"  #{alvo}: {r.get('status_anterior')} -> {r.get('status_novo')}")
            print(f"  mensagem: {r.get('mensagem')}")
            if not r.get("atualizado"):
                falhas.append("mudança de status não foi aplicada")

            # 12. Persistiu? Reconsulta pelo protocolo.
            titulo("12. Persistência — o status mudou mesmo?")
            chamado = (await cliente.call_tool(
                "buscar_historico_cliente", {"cliente": abertos[0]["cliente"]}
            )).data
            atual = next(c for c in chamado["chamados"] if c["id"] == alvo)
            print(f"  status atual = {atual['status']}  histórico = {len(atual['historico'])} evento(s)")
            if atual["status"] != "em_andamento":
                falhas.append("a mudança não persistiu no banco")
            if len(atual["historico"]) != 1:
                falhas.append("a mudança não foi registrada no histórico")

            # 13. Mesmo status de novo: nada deve mudar.
            titulo("13. atualizar_status — repetir o mesmo status")
            r = (await cliente.call_tool(
                "atualizar_status", {"chamado_id": alvo, "novo_status": "em_andamento"}
            )).data
            print(f"  atualizado = {r.get('atualizado')}  msg: {r.get('mensagem')}")
            if r.get("atualizado") is not False:
                falhas.append("repetir o mesmo status deveria registrar atualizado=false")

            # 14. O histórico acumula ao longo de mudanças sucessivas.
            titulo("14. Histórico acumula em mudanças sucessivas")
            for novo in ("fechado", "aberto"):
                await cliente.call_tool(
                    "atualizar_status", {"chamado_id": alvo, "novo_status": novo}
                )
            chamado = (await cliente.call_tool(
                "buscar_historico_cliente", {"cliente": abertos[0]["cliente"]}
            )).data
            atual = next(c for c in chamado["chamados"] if c["id"] == alvo)
            print(f"  histórico = {len(atual['historico'])} eventos (esperado: 3)")
            for h in atual["historico"]:
                print(f"    {h['status_anterior']} -> {h['status_novo']}")
            if len(atual["historico"]) != 3:
                falhas.append("o histórico não acumulou as mudanças")
        else:
            falhas.append("não há chamados abertos para atualizar")

    titulo("Resultado")
    if falhas:
        for f in falhas:
            print(f"  ✗ {f}")
        return 1
    print("  Todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
