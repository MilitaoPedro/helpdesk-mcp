"""Acesso ao banco SQLite do helpdesk.

Responsável por criar, popular e consultar o banco de chamados. A criação e o
povoamento são idempotentes: rodar a inicialização várias vezes não apaga nem
duplica dados.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Caminho padrão do banco: um arquivo na raiz do projeto.
CAMINHO_PADRAO = Path(__file__).resolve().parent.parent / "helpdesk.db"

# Status aceitos. Definição única, compartilhada pelas três ferramentas.
STATUS_VALIDOS = ("aberto", "em_andamento", "fechado")


def _agora() -> str:
    """Data/hora atual em ISO 8601 (UTC), usada em criado_em/atualizado_em."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _resolver(caminho: Path | str | None) -> Path | str:
    """Resolve o caminho do banco.

    O padrão é lido no momento da chamada, e não capturado como valor padrão do
    argumento: valores padrão são avaliados uma única vez, na definição da
    função, o que impediria testes (e configurações) de apontarem o banco para
    outro arquivo depois do import.
    """
    return CAMINHO_PADRAO if caminho is None else caminho


def conectar(caminho: Path | str | None = None) -> sqlite3.Connection:
    """Abre uma conexão com o banco, criando o arquivo se necessário."""
    conexao = sqlite3.connect(str(_resolver(caminho)))
    conexao.row_factory = sqlite3.Row  # permite acessar colunas por nome
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def _criar_tabelas(conexao: sqlite3.Connection) -> None:
    """Cria as tabelas do projeto, se ainda não existirem."""
    conexao.executescript(
        """
        CREATE TABLE IF NOT EXISTS chamados (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente       TEXT    NOT NULL,
            descricao     TEXT    NOT NULL,
            status        TEXT    NOT NULL,
            criado_em     TEXT    NOT NULL,
            atualizado_em TEXT    NOT NULL
        );

        -- Registra cada mudança de status, para que o histórico de um
        -- chamado não se perca quando o status atual muda.
        CREATE TABLE IF NOT EXISTS historico_status (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            chamado_id      INTEGER NOT NULL,
            status_anterior TEXT,
            status_novo     TEXT    NOT NULL,
            alterado_em     TEXT    NOT NULL,
            FOREIGN KEY (chamado_id) REFERENCES chamados (id)
        );
        """
    )


# Dados fictícios. Nenhum dado real de cliente é usado.
# Inclui um cliente com mais de um chamado (usado na Fase 2) e cobre os três status.
_CHAMADOS_FICTICIOS = [
    # (cliente, descricao, status, dias_atras)
    ("Ana Souza", "Notebook não liga após queda de energia", "aberto", 0),
    ("Ana Souza", "Impressora do 2º andar sem conexão", "em_andamento", 2),
    ("Bruno Lima", "Solicitação de acesso ao sistema de folha", "aberto", 1),
    ("Carla Mendes", "Erro ao emitir relatório mensal", "fechado", 9),
    ("Diego Rocha", "E-mail corporativo não sincroniza no celular", "em_andamento", 3),
    ("Elisa Prado", "Troca de monitor com defeito na tela", "fechado", 6),
]


def _popular(conexao: sqlite3.Connection) -> int:
    """Insere os chamados fictícios. Retorna quantos foram inseridos."""
    agora = datetime.now(timezone.utc)

    registros = []
    for cliente, descricao, status, dias_atras in _CHAMADOS_FICTICIOS:
        # Datas escalonadas para que a ordenação por criado_em seja significativa.
        criado = (agora - timedelta(days=dias_atras)).isoformat(timespec="seconds")
        registros.append((cliente, descricao, status, criado, criado))

    conexao.executemany(
        """
        INSERT INTO chamados (cliente, descricao, status, criado_em, atualizado_em)
        VALUES (?, ?, ?, ?, ?)
        """,
        registros,
    )
    return len(registros)


def inicializar(caminho: Path | str | None = None) -> sqlite3.Connection:
    """Garante que o banco existe, tem as tabelas e está populado.

    Idempotente: se já houver chamados, não altera nem apaga nada.
    """
    conexao = conectar(caminho)
    _criar_tabelas(conexao)

    total = conexao.execute("SELECT COUNT(*) FROM chamados").fetchone()[0]
    if total == 0:
        _popular(conexao)
        conexao.commit()

    return conexao


def listar(status: str | None = None, caminho: Path | str | None = None) -> list[dict]:
    """Retorna os chamados, do mais recente para o mais antigo.

    Com `status` informado, filtra por ele. Lista vazia é um resultado legítimo
    e não um erro.
    """
    conexao = inicializar(caminho)
    try:
        if status is None:
            linhas = conexao.execute(
                "SELECT * FROM chamados ORDER BY criado_em DESC, id DESC"
            ).fetchall()
        else:
            linhas = conexao.execute(
                "SELECT * FROM chamados WHERE status = ? ORDER BY criado_em DESC, id DESC",
                (status,),
            ).fetchall()
        return [dict(linha) for linha in linhas]
    finally:
        conexao.close()
