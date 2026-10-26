"""Lógica de atendimento: texto do atendente -> resposta em markdown.

Concentra a interpretação do comando e a chamada às ferramentas MCP, devolvendo
texto. Fica separado do `app.py` por dois motivos:

1. o Streamlit reexecuta o script inteiro a cada interação, e resultados
   renderizados como widgets não sobrevivem entre reruns. Devolvendo markdown,
   a resposta é guardada no histórico e reaparece corretamente;
2. sem depender do Streamlit, esta lógica pode ser testada diretamente.
"""

from __future__ import annotations

import comandos as cmds
import mcp_client


def _erro(mensagem: str) -> str:
    return f"❌ {mensagem}"


def _aviso(mensagem: str) -> str:
    return f"⚠️ {mensagem}"


def _tabela_chamados(chamados: list[dict]) -> str:
    """Tabela markdown com os chamados."""
    linhas = [
        "| ID | Cliente | Descrição | Status | Aberto em |",
        "| --- | --- | --- | --- | --- |",
    ]
    for c in chamados:
        linhas.append(
            f"| {c['id']} | {c['cliente']} | {c['descricao']} | "
            f"`{c['status']}` | {c['criado_em'][:10]} |"
        )
    return "\n".join(linhas)


def _bloco_historico(chamados: list[dict]) -> str:
    """Chamados de um cliente, cada um com seu histórico de status."""
    partes = []
    for c in chamados:
        partes.append(
            f"**#{c['id']} — {c['cliente']}** · status: `{c['status']}`  \n"
            f"{c['descricao']}"
        )
        if c["historico"]:
            partes.append("Histórico de status:")
            for h in c["historico"]:
                anterior = h["status_anterior"] or "—"
                partes.append(
                    f"- `{anterior}` → `{h['status_novo']}` ({h['alterado_em'][:19]})"
                )
        else:
            partes.append("_Sem mudanças de status registradas._")
        partes.append("")
    return "\n\n".join(partes)


def responder(texto: str) -> str:
    """Interpreta o texto e devolve a resposta em markdown.

    Nunca levanta exceção: erros de comando e de comunicação com o servidor
    viram mensagens legíveis para o atendente.
    """
    try:
        comando = cmds.interpretar(texto)
    except cmds.ComandoInvalido as erro:
        return _aviso(str(erro))

    try:
        return _executar(comando)
    except mcp_client.ErroMCP as erro:
        return _erro(f"Erro ao falar com o servidor MCP: {erro}")


def _executar(comando: cmds.Comando) -> str:
    argumentos = dict(comando.argumentos)
    cabecalho = f"`{comando.ferramenta}` · {comando.descricao}\n\n"

    # "histórico do cliente 2": o número é o id de um chamado. Resolve para o
    # nome do cliente antes de chamar a ferramenta, que trabalha com nomes.
    if comando.resolver_cliente_por_chamado:
        chamado_id = int(argumentos["cliente"])
        chamado = next(
            (
                c
                for c in mcp_client.listar_chamados()["chamados"]
                if c["id"] == chamado_id
            ),
            None,
        )
        if chamado is None:
            return cabecalho + _erro(f"Chamado {chamado_id} não encontrado.")
        argumentos["cliente"] = chamado["cliente"]
        cabecalho += (
            f"_Chamado {chamado_id} é do cliente **{chamado['cliente']}**._\n\n"
        )

    if comando.ferramenta == "ajuda":
        return cmds.AJUDA

    if comando.ferramenta == "listar_chamados":
        r = mcp_client.listar_chamados(argumentos.get("status"))
        if "erro" in r:
            return cabecalho + _erro(r["erro"])
        if r["total"] == 0:
            return cabecalho + _aviso("Nenhum chamado encontrado.")
        return cabecalho + f"**{r['total']} chamado(s).**\n\n" + _tabela_chamados(
            r["chamados"]
        )

    if comando.ferramenta == "buscar_historico_cliente":
        r = mcp_client.buscar_historico_cliente(argumentos["cliente"])
        if "erro" in r:
            return cabecalho + _erro(r["erro"])
        if r["total"] == 0:
            return cabecalho + _aviso(
                f"Nenhum chamado encontrado para {argumentos['cliente']!r}."
            )
        resumo = r["resumo"]["por_status"]
        return (
            cabecalho
            + f"**{r['total']} chamado(s) de {r['cliente']}.**\n\n"
            + f"_Resumo por status: {resumo}_\n\n"
            + _bloco_historico(r["chamados"])
        )

    if comando.ferramenta == "atualizar_status":
        r = mcp_client.atualizar_status(
            argumentos["chamado_id"], argumentos["novo_status"]
        )
        if "erro" in r:
            return cabecalho + _erro(r["erro"])
        if r["atualizado"]:
            return cabecalho + f"✅ {r['mensagem']}"
        return cabecalho + _aviso(r["mensagem"])

    return cabecalho + _erro(f"Comando sem execução implementada: {comando.ferramenta}")
