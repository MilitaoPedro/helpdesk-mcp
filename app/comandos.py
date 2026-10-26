"""Interpretação dos comandos digitados pelo atendente.

Aqui não há modelo de linguagem: o texto é casado contra um conjunto fixo de
padrões e convertido em uma chamada de ferramenta MCP. Isso mantém o
comportamento previsível e verificável — o protótipo é uma interface de chat
que opera MCP, e não um agente conversacional.

Fica separado do app para poder ser testado sem subir o Streamlit.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Sinônimos aceitos para cada status, normalizados (sem acento, minúsculos).
_STATUS_POR_PALAVRA = {
    "aberto": "aberto",
    "abertos": "aberto",
    "em andamento": "em_andamento",
    "andamento": "em_andamento",
    "em_andamento": "em_andamento",
    "fechado": "fechado",
    "fechados": "fechado",
    "encerrado": "fechado",
    "encerrados": "fechado",
    "concluido": "fechado",
    "concluidos": "fechado",
}

_STATUS_DESCRITOS = "aberto, em_andamento ou fechado"


@dataclass
class Comando:
    """Um comando reconhecido e os argumentos para a ferramenta MCP."""

    ferramenta: str
    argumentos: dict
    descricao: str
    # Verdadeiro quando o atendente informou o número de um chamado no lugar do
    # nome do cliente. O app resolve o número para o nome antes de chamar a
    # ferramenta, que trabalha com nomes.
    resolver_cliente_por_chamado: bool = False


class ComandoInvalido(ValueError):
    """O texto digitado não corresponde a nenhum comando conhecido."""


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e sem espaços nas pontas."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return " ".join(sem_acento.lower().split())


def _status_para_valor(texto: str) -> str | None:
    """Converte o texto digitado em um status válido, ou None."""
    return _STATUS_POR_PALAVRA.get(normalizar(texto))


def _texto_original_apos(texto: str, padrao: str) -> str:
    """Extrai o trecho após `padrao`, preservando a grafia original.

    Casa o padrão sobre o texto normalizado, mas devolve o trecho
    correspondente do texto como o atendente digitou — útil para exibir nomes
    próprios com a capitalização correta.
    """
    m = re.search(padrao + r"(.+)$", normalizar(texto))
    if not m:
        return ""
    # O normalizado colapsa espaços, então a posição pode não bater; busca o
    # trecho original pelo conteúdo, sem diferenciar caixa.
    alvo = m.group(1).strip()
    return _recuperar_grafia(texto, alvo)


def _recuperar_grafia(original: str, normalizado_alvo: str) -> str:
    """Encontra em `original` o trecho que, normalizado, dá `normalizado_alvo`."""
    palavras_originais = original.split()
    palavras_alvo = normalizado_alvo.split()
    n = len(palavras_alvo)

    for inicio in range(len(palavras_originais) - n + 1):
        trecho = palavras_originais[inicio : inicio + n]
        if normalizar(" ".join(trecho)) == normalizado_alvo:
            return " ".join(trecho)
    return normalizado_alvo


def interpretar(texto: str) -> Comando:
    """Converte o texto do atendente em um comando.

    Levanta ComandoInvalido se o texto não for reconhecido.
    """
    if not texto or not texto.strip():
        raise ComandoInvalido("Digite um comando.")

    t = normalizar(texto)

    # "ajuda" / "help"
    if t in {"ajuda", "help", "?", "socorro"}:
        return Comando("ajuda", {}, "Mostra os comandos disponíveis")

    # "alterar chamado 3 para fechado"
    # "mudar o status do chamado 12 para em andamento"
    m = re.search(
        r"(?:alterar|altere|mudar|mude|atualizar|atualize|trocar|troque)"
        r".*?(?:chamado\D*)?(\d+)\s*(?:para|pra|pro|->|=>)\s*(.+)$",
        t,
    )
    if m:
        chamado_id = int(m.group(1))
        status = _status_para_valor(m.group(2))
        if status is None:
            raise ComandoInvalido(
                f"Status não reconhecido: {m.group(2).strip()!r}. "
                f"Use um destes: {_STATUS_DESCRITOS}."
            )
        return Comando(
            "atualizar_status",
            {"chamado_id": chamado_id, "novo_status": status},
            f"Altera o chamado {chamado_id} para {status}",
        )

    # "historico do cliente 2" / "historico da ana souza"
    # / "chamados do cliente bruno lima"
    # \b evita que "dos" case dentro de "chamados".
    m = re.search(
        r"\b(?:historico|chamados?)\s*\b(?:do|da|de|dos|das)\s*"
        r"(?:cliente\s*)?(.+)$",
        t,
    )
    if m:
        # O nome sai do texto original (e não do normalizado) para que a
        # resposta exiba "Ana Souza" e não "ana souza". A busca no banco já é
        # insensível a maiúsculas/minúsculas.
        alvo = _texto_original_apos(
            texto, r"\b(?:do|da|de|dos|das)\s*(?:cliente\s*)?"
        )
        if not alvo:
            raise ComandoInvalido("Informe o cliente.")

        # "histórico do cliente 2": um número aqui é o id de um chamado, como
        # no exemplo dos slides. O app resolve o id para o nome do cliente.
        if alvo.isdigit():
            return Comando(
                "buscar_historico_cliente",
                {"cliente": alvo},
                f"Busca o histórico do cliente do chamado {alvo}",
                resolver_cliente_por_chamado=True,
            )

        return Comando(
            "buscar_historico_cliente",
            {"cliente": alvo},
            f"Busca o histórico do cliente {alvo!r}",
        )

    # "listar abertos" / "lista todos" / "listar chamados em andamento"
    m = re.search(r"(?:listar|lista|listar|mostrar|mostra|ver|exibir|exibe)\b(.*)$", t)
    if m:
        resto = m.group(1).strip()
        # Remove preenchimentos: "os chamados", "chamados", "todos os".
        resto = re.sub(r"^(?:os|as|todos os|todas as|o|a)?\s*chamados?\s*", "", resto)
        resto = re.sub(r"^(?:todos|todas)\s*", "", resto)
        resto = resto.strip()
        resto = re.sub(r"^(?:com status|de status|status)\s*", "", resto).strip()

        if not resto or resto in {"todos", "tudo", "all"}:
            return Comando("listar_chamados", {}, "Lista todos os chamados")

        status = _status_para_valor(resto)
        if status is not None:
            return Comando(
                "listar_chamados",
                {"status": status},
                f"Lista os chamados com status {status}",
            )
        raise ComandoInvalido(
            f"Não entendi {resto!r}. Use um destes status: {_STATUS_DESCRITOS}, "
            "ou 'listar todos'."
        )

    raise ComandoInvalido(
        "Comando não reconhecido. Digite 'ajuda' para ver os comandos disponíveis."
    )


AJUDA = """\
**Comandos disponíveis**

| Comando | O que faz |
| --- | --- |
| `listar todos` | Lista todos os chamados |
| `listar abertos` | Lista os chamados abertos |
| `listar em andamento` | Lista os chamados em andamento |
| `listar fechados` | Lista os chamados fechados |
| `histórico do cliente <nome>` | Chamados do cliente e histórico de cada um |
| `alterar chamado <id> para <status>` | Muda o status (única operação de escrita) |

Status aceitos: `aberto`, `em_andamento`, `fechado`.
"""
