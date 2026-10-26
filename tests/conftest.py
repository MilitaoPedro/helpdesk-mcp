"""Configuração comum dos testes."""

import sys
from pathlib import Path

import pytest

# Permite importar `helpdesk` e `servidor` a partir da raiz do projeto.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpdesk import banco  # noqa: E402


@pytest.fixture
def banco_temporario(tmp_path, monkeypatch):
    """Isola cada teste em um banco temporário próprio.

    Aponta o caminho padrão do banco para um arquivo em tmp_path, de modo que
    os testes nunca toquem no helpdesk.db de desenvolvimento.
    """
    caminho = tmp_path / "teste.db"
    monkeypatch.setattr(banco, "CAMINHO_PADRAO", caminho)
    return caminho


@pytest.fixture
def banco_populado(banco_temporario):
    """Um banco já criado e populado com os dados fictícios."""
    conexao = banco.inicializar(banco_temporario)
    conexao.close()
    return banco_temporario
