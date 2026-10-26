# Fase 1 — `listar_chamados`: requisitos

## Objetivo

Criar a base do servidor MCP (processo, banco SQLite e dados fictícios) e expor a primeira
ferramenta: `listar_chamados`.

## Comportamentos

**R1 — Listar todos os chamados.**
Quando chamada sem filtro, a ferramenta retorna **todos** os chamados do banco.

**R2 — Filtrar por status.**
Quando chamada com um status, retorna apenas os chamados com aquele status.

**R3 — Filtro sem resultados.**
Quando o filtro não corresponde a nenhum chamado, retorna uma **lista vazia**, sem erro.
Este é um resultado legítimo: significa "não há chamados nesse status".

**R4 — Status inválido é rejeitado.**
Se o filtro não for um dos três status aceitos (`aberto`, `em_andamento`, `fechado`), a
ferramenta retorna um erro explicativo, listando os valores válidos.

Este requisito foi decidido durante a especificação: sem ele, um erro de digitação como
`"abertos"` retornaria uma lista vazia e seria indistinguível de "não há chamados abertos" —
um falso negativo silencioso. Distinguir os dois casos é o que torna a ferramenta confiável
para um agente.

**R5 — Banco criado e populado automaticamente.**
Na primeira execução, o banco é criado e populado com registros fictícios, para que a
ferramenta tenha o que retornar sem nenhuma preparação manual.

**R6 — Inicialização não destrutiva.**
Se o banco já existe e contém chamados, a inicialização **não altera nem apaga** nada.

## Entradas

| Parâmetro | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `status` | texto ou ausente | não | Filtra os chamados pelo status informado |

## Saídas

Um objeto com:

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `total` | inteiro | Quantidade de chamados retornados |
| `chamados` | lista | Os chamados encontrados, do mais recente para o mais antigo |

Cada item de `chamados` contém: `id`, `cliente`, `descricao`, `status`, `criado_em`,
`atualizado_em`.

Em caso de erro (R4), o objeto contém `erro` (mensagem) e `status_validos` (a lista de valores
aceitos).

## Casos relevantes

| # | Situação | Resultado esperado |
| --- | --- | --- |
| 1 | Chamada sem filtro | Todos os chamados do banco (R1) |
| 2 | Filtro `aberto` | Apenas chamados abertos (R2) |
| 3 | Filtro `fechado` | Apenas chamados fechados (R2) |
| 4 | Filtro com status válido sem chamados | `total = 0` e lista vazia (R3) |
| 5 | Filtro `"abertos"` (inválido) | Erro com a lista de status válidos (R4) |
| 6 | Banco inexistente | Banco criado e populado (R5) |
| 7 | Banco existente com dados | Nada é apagado (R6) |

## Dados fictícios (seed)

Clientes e chamados inventados, cobrindo os três status — o suficiente para exercitar todos
os casos acima, incluindo ao menos um cliente com mais de um chamado (útil na Fase 2).
