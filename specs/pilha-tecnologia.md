# Pilha tecnológica

Decisões técnicas do projeto. Cada escolha abaixo é uma **restrição** que as fases de
implementação devem respeitar.

## Linguagem e ambiente

**Python 3.10+** (desenvolvido e validado em Python 3.14) com **ambiente virtual** isolado.

O ambiente virtual é obrigatório: `fastmcp` e `streamlit` não devem ser instalados no Python
do sistema. As dependências ficam declaradas em [`requirements.txt`](../requirements.txt) e a
instalação é documentada no README.

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> **Importante:** o comando Python registrado no cliente MCP precisa apontar para o Python
> **do ambiente virtual** (`.venv/bin/python`), e não para o Python do sistema — caso contrário
> a biblioteca `fastmcp` não será encontrada na inicialização do servidor.

## Biblioteca MCP

**`fastmcp` (4.1.3)**, que fornece tanto a classe `FastMCP` para construir o servidor quanto o
`Client` usado pelo app da Parte 2 para consumi-lo.

```python
from fastmcp import FastMCP

mcp = FastMCP("Helpdesk")

@mcp.tool()
def listar_chamados(status: str | None = None) -> dict:
    ...

mcp.run()
```

Observações de implementação verificadas na versão 4.1.3:

- `FastMCP` e `Client` são importáveis diretamente de `fastmcp`.
- `mcp.run()` usa **stdio** por padrão, que é o transporte definido para este projeto.
- Para conectar o client a um script local, usa-se `PythonStdioTransport(script_path=...)`;
  a inferência a partir de uma string de comando não é suportada nesta versão.
- Em `stdio`, **nada além do protocolo pode ser escrito em `stdout`**. Mensagens de depuração
  devem ir para `stderr` (ou usar `logging`), pois um `print()` em `stdout` corrompe a
  comunicação JSON-RPC.

## Persistência

**SQLite** através do módulo `sqlite3` da biblioteca padrão — sem dependência externa e sem
servidor de banco de dados para instalar.

- O banco é um único arquivo (`helpdesk.db`) no diretório do projeto.
- O arquivo é criado automaticamente e **populado com registros fictícios** na primeira
  execução, caso ainda não exista.
- A inicialização **não apaga dados existentes**: se o banco já tiver chamados, nada é
  sobrescrito. Isso protege alterações feitas durante o uso.
- O arquivo `.db` **não é versionado** (ver `.gitignore`): ele é gerado a partir do código.

### Estrutura

**`chamados`** — o registro de cada chamado:

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `id` | INTEGER PK | Identificador do chamado |
| `cliente` | TEXT | Nome do cliente |
| `descricao` | TEXT | Descrição do problema |
| `status` | TEXT | Status atual (ver abaixo) |
| `criado_em` | TEXT | Data/hora de abertura (ISO 8601) |
| `atualizado_em` | TEXT | Data/hora da última alteração (ISO 8601) |

**`historico_status`** — o registro de cada mudança de status, para que o histórico de um
chamado não seja perdido quando seu status muda:

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `id` | INTEGER PK | Identificador do evento |
| `chamado_id` | INTEGER FK | Chamado alterado |
| `status_anterior` | TEXT | Status antes da mudança |
| `status_novo` | TEXT | Status depois da mudança |
| `alterado_em` | TEXT | Data/hora da alteração (ISO 8601) |

### Status aceitos

Conjunto fechado de três valores, em texto:

| Valor | Significado |
| --- | --- |
| `aberto` | Chamado registrado, ainda não atendido |
| `em_andamento` | Chamado em atendimento |
| `fechado` | Chamado encerrado |

Usar um conjunto fechado permite validar entradas e evita variações como `Aberto`, `ABERTO`
ou `open`, que quebrariam os filtros. Textos sem acento e em minúsculas evitam problemas de
codificação em diferentes terminais.

## Execução

**Local, via `stdio`.** O servidor é iniciado como um processo filho pelo cliente MCP, e a
comunicação acontece pelos canais padrão de entrada e saída.

Não há servidor HTTP, porta de rede ou publicação externa. Consequência direta: o servidor
não deve escrever nada em `stdout` além das mensagens do protocolo.
