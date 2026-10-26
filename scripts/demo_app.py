"""Validação do app: a mesma lógica da interface, chamada pelo protocolo MCP.

Exercita `app/atendimento.py` — exatamente o caminho que o Streamlit usa — sem
subir o servidor web. Cada resposta aqui é o texto markdown que o atendente
veria na tela, e cada uma vem de uma chamada MCP real ao `servidor.py`.

Requisito que este script comprova: o app **não** acessa o SQLite. Todo dado
exibido passou pelo servidor MCP.

Uso:
    python scripts/demo_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "app"))

import atendimento  # noqa: E402

# Comandos como o atendente digitaria, cobrindo os três casos de uso.
COMANDOS = [
    "listar abertos",
    "listar todos",
    "histórico do cliente Ana Souza",
    "alterar chamado 1 para em_andamento",
    "listar em andamento",
    "alterar chamado 1 para em_andamento",   # repetido: nada deve mudar
    "alterar chamado 99999 para fechado",    # inexistente
    "alterar chamado 1 para roxo",           # status inválido
    "histórico do cliente Cliente Inexistente",
    "conversa fiada",                        # comando não reconhecido
]


def titulo(texto: str) -> None:
    print(f"\n{'=' * 66}\n{texto}\n{'=' * 66}")


def main() -> int:
    for comando in COMANDOS:
        titulo(f"Atendente: {comando}")
        resposta = atendimento.responder(comando)
        print(resposta)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
