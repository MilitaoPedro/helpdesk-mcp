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

Instruções de instalação e execução são adicionadas ao final da implementação.
