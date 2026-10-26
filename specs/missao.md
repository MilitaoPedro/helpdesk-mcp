# Missão do projeto

## Problema

Uma equipe de suporte registra os chamados de seus clientes em um banco de dados. Hoje, obter
respostas como "quais chamados estão abertos?" ou "qual o histórico do cliente X?" exige que
alguém consulte o banco manualmente ou use um sistema com interface própria.

Isso cria dois problemas: o atendimento depende de uma pessoa para cada consulta, e agentes de
IA não conseguem acessar esses dados de forma padronizada para ajudar no atendimento.

## Propósito

O `helpdesk-mcp` é um **servidor MCP** que expõe as operações de consulta e atualização desses
chamados como *ferramentas* padronizadas. Assim, qualquer agente ou aplicação compatível com
MCP consegue:

- listar chamados, opcionalmente filtrando por status;
- consultar o histórico de chamados de um cliente;
- atualizar o status de um chamado.

O projeto **não** é um sistema de atendimento com interface própria. Ele é a camada de acesso
aos dados — um conjunto de operações que um agente pode executar.

## Quem usa

O consumidor direto são **agentes e aplicações clientes de MCP**, por exemplo:

- um agente de IA em um editor de código que responde a perguntas sobre os chamados;
- o protótipo Streamlit deste repositório, que interpreta comandos de um atendente.

Não há usuário final humano interagindo diretamente com o servidor: toda interação passa por um
cliente MCP.

## Escopo inicial

**Dentro do escopo:**

- listagem de chamados com filtro opcional por status;
- consulta ao histórico de chamados de um cliente;
- atualização do status de um chamado.

**Fora do escopo:**

- criação e exclusão de chamados;
- autenticação e controle de permissões;
- interface de atendente no servidor (a interface é um protótipo separado, na Parte 2);
- integração com sistemas reais de suporte.

## Limites e premissas

- **Dados fictícios.** O banco é populado com registros inventados. Nenhum dado real de cliente
  é usado, armazenado ou versionado.
- **Uso local.** O servidor roda na máquina do desenvolvedor, via `stdio`, e não é publicado
  na internet.
- **Sem autenticação real.** Não há login, token ou controle de acesso. Qualquer cliente que
  consiga iniciar o processo do servidor tem acesso total às ferramentas.
- **Persistência local em SQLite.** O banco é um arquivo no disco do projeto, recriado e
  populado automaticamente quando não existe.
