# helpdesk-mcp

Servidor **MCP** (Model Context Protocol) que expõe operações de um sistema de helpdesk —
consulta e atualização de chamados — para agentes de IA, além de um protótipo de interface
**Streamlit** que consome esse servidor.

Projeto da disciplina **GAC126 / PASIA — Aula P.10** (DAC-ICET-UFLA).

> **Status:** em desenvolvimento. A constituição do projeto (missão, pilha tecnológica e
> roadmap) está em [`specs/`](specs/), e cada funcionalidade possui sua própria especificação.

## O que é MCP

O Model Context Protocol é um padrão aberto, criado pela Anthropic, para conectar aplicações
de IA a fontes de dados e ferramentas externas — uma espécie de "USB-C para aplicações de IA".
A comunicação usa JSON-RPC e os servidores podem expor três tipos de capacidade: **Tools**
(ações que o agente pode executar), **Resources** (dados que o agente pode ler) e **Prompts**
(modelos de instrução reutilizáveis).

Este projeto expõe apenas **Tools**, porque o objetivo é permitir que um agente execute
operações sobre os dados de chamados, e não fornecer uma interface de atendente.

## Escopo

O servidor expõe três ferramentas sobre um banco SQLite local com dados fictícios:

| Ferramenta | O que faz |
| --- | --- |
| `listar_chamados` | Lista os chamados, com filtro opcional por status |
| `buscar_historico_cliente` | Retorna os chamados de um cliente e o histórico de mudanças de status |
| `atualizar_status` | Altera o status de um chamado, registrando a mudança no histórico |

## Documentação

- [`specs/missao.md`](specs/missao.md) — propósito e limites do projeto
- [`specs/pilha-tecnologia.md`](specs/pilha-tecnologia.md) — decisões técnicas e restrições
- [`specs/roadmap.md`](specs/roadmap.md) — fases de implementação

## Instalação

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Execução

### Testes

```bash
.venv/bin/python -m pytest tests/ -v
```

Os testes usam um banco temporário próprio e não afetam o `helpdesk.db` de desenvolvimento.

### Servidor MCP

```bash
.venv/bin/python servidor.py
```

O servidor usa o transporte `stdio` e é iniciado pelo cliente MCP — normalmente você não o
executa à mão. O banco `helpdesk.db` é criado e populado com dados fictícios na primeira
execução.

O banco guarda as alterações feitas durante o uso: depois de atualizar status, ele deixa de
estar no estado inicial. Para voltar aos dados fictícios originais, apague o arquivo — ele é
recriado na próxima execução:

```bash
rm -f helpdesk.db
```

### Registro em um cliente MCP

O repositório traz duas configurações de registro:

- [`.vscode/mcp.json`](.vscode/mcp.json) — lido pelo VS Code, que ativa o servidor
  automaticamente ao abrir o projeto;
- [`.mcp.json`](.mcp.json) — formato usado por outros clientes MCP.

Ambas apontam para o Python **do ambiente virtual** deste projeto. Se o seu cliente não
entender `${workspaceFolder}`, troque pelo caminho absoluto:

```json
{
  "mcpServers": {
    "helpdesk": {
      "type": "stdio",
      "command": "/caminho/para/helpdesk-mcp/.venv/bin/python",
      "args": ["/caminho/para/helpdesk-mcp/servidor.py"]
    }
  }
}
```

### Verificação ponta a ponta

Chama o servidor pelo protocolo MCP, como um cliente real:

```bash
.venv/bin/python scripts/demo_mcp.py
```

## Ferramentas

### `listar_chamados`

Lista os chamados, com filtro opcional por status.

| Parâmetro | Tipo | Descrição |
| --- | --- | --- |
| `status` | texto, opcional | `aberto`, `em_andamento` ou `fechado` |

Retorna `total` e `chamados` (do mais recente para o mais antigo). Status inválido retorna
`erro` e `status_validos`. Exemplos:

```python
listar_chamados()                      # todos os chamados
listar_chamados(status="aberto")       # apenas os abertos
```

### `buscar_historico_cliente`

Retorna os chamados de um cliente e o histórico de mudanças de status de cada um.

| Parâmetro | Tipo | Descrição |
| --- | --- | --- |
| `cliente` | texto | Nome do cliente (obrigatório) |

A busca ignora maiúsculas/minúsculas e espaços nas pontas, mas não encontra nomes parciais.
Retorna `cliente`, `total`, `resumo` (contagem por status) e `chamados` — cada chamado com seu
campo `historico`. Cliente sem chamados retorna `total = 0`; nome vazio retorna `erro`.

```python
buscar_historico_cliente("Ana Souza")   # chamados da Ana + histórico de cada um
```

### `atualizar_status`

Altera o status de um chamado e registra a mudança no histórico. É a **única** ferramenta que
modifica dados.

| Parâmetro | Tipo | Descrição |
| --- | --- | --- |
| `chamado_id` | inteiro | Identificador do chamado |
| `novo_status` | texto | `aberto`, `em_andamento` ou `fechado` |

Retorna `atualizado`, `chamado_id`, `status_anterior`, `status_novo` e `mensagem`. Se o
chamado já estava no status informado, retorna `atualizado = false` sem registrar nada.
Status inválido ou chamado inexistente retornam `erro`, sem alterar o banco.

```python
atualizar_status(1, "em_andamento")     # atualiza e registra no histórico
atualizar_status(1, "em_andamento")     # já estava: atualizado = false
```

Cada mudança efetiva é registrada em `historico_status` e **nada é sobrescrito**: o histórico
de um chamado acumula ao longo do tempo.

## Exemplos de execução

Saídas reais das ferramentas, sobre os dados fictícios do banco recém-criado
(`rm -f helpdesk.db` antes, para partir do estado inicial).

### `listar_chamados(status="aberto")`

```json
{
  "total": 2,
  "chamados": [
    {
      "id": 1,
      "cliente": "Ana Souza",
      "descricao": "Notebook não liga após queda de energia",
      "status": "aberto",
      "criado_em": "2026-10-26T01:59:24+00:00",
      "atualizado_em": "2026-10-26T01:59:24+00:00"
    },
    {
      "id": 3,
      "cliente": "Bruno Lima",
      "descricao": "Solicitação de acesso ao sistema de folha",
      "status": "aberto",
      "criado_em": "2026-10-25T01:59:24+00:00",
      "atualizado_em": "2026-10-25T01:59:24+00:00"
    }
  ]
}
```

### `buscar_historico_cliente("Ana Souza")`

Depois de o chamado 1 ter passado por `aberto` → `em_andamento` → `fechado`. O histórico
acumula os dois eventos:

```json
{
  "id": 1,
  "cliente": "Ana Souza",
  "descricao": "Notebook não liga após queda de energia",
  "status": "fechado",
  "historico": [
    {
      "status_anterior": "aberto",
      "status_novo": "em_andamento",
      "alterado_em": "2026-10-26T02:00:28.810692+00:00"
    },
    {
      "status_anterior": "em_andamento",
      "status_novo": "fechado",
      "alterado_em": "2026-10-26T02:00:28.812264+00:00"
    }
  ]
}
```

### `atualizar_status(1, "fechado")`

```json
{
  "atualizado": true,
  "chamado_id": 1,
  "status_anterior": "em_andamento",
  "status_novo": "fechado",
  "mensagem": "Chamado 1: status alterado de 'em_andamento' para 'fechado'."
}
```

Repetir a mesma chamada devolve `"atualizado": false`, sem registrar nada novo.

## Interface de atendimento (Streamlit)

O diretório [`app/`](app/) contém um protótipo de interface de chat para o atendente.

```bash
.venv/bin/python -m streamlit run app/app.py
```

A interface abre em `http://localhost:8501`. Exemplos de comandos:

```
listar abertos
listar em andamento
histórico do cliente Ana Souza
alterar chamado 3 para fechado
ajuda
```

### Como funciona

```
atendente → app Streamlit → client MCP (stdio) → servidor MCP → SQLite
```

O app é um **cliente MCP**: ele não abre o banco de dados. Toda consulta e alteração passa
pelo servidor, pelo protocolo MCP — é isso que o protótipo demonstra.

**Não há modelo de linguagem aqui.** O texto digitado é casado contra um conjunto fixo de
padrões (`app/comandos.py`) e convertido em chamadas de ferramenta. É uma interface de chat
que opera MCP, e não um agente conversacional — o comportamento é previsível e testável. A
extensão opcional dos slides (perguntas em linguagem livre, com um modelo escolhendo a
ferramenta) não foi implementada.

Para exercitar a mesma lógica sem abrir o navegador:

```bash
.venv/bin/python scripts/demo_app.py
```
