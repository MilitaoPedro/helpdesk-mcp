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

### Registro em um cliente MCP

O arquivo [`.mcp.json`](.mcp.json) na raiz registra o servidor. Ajuste o caminho absoluto do
comando para o Python **do ambiente virtual** deste projeto:

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
