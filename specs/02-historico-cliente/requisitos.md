# Fase 2 — `buscar_historico_cliente`: requisitos

## Objetivo

Expor a ferramenta `buscar_historico_cliente`, que reúne tudo o que se sabe sobre o
atendimento a um cliente: os chamados dele e o histórico de mudanças de status de cada um.

## Comportamentos

**R1 — Todos os chamados do cliente.**
Retorna os chamados cujo `cliente` corresponde ao informado, do mais recente para o mais antigo.

**R2 — Histórico de cada chamado.**
Junto de cada chamado, retorna a lista de mudanças de status registradas para ele
(`status_anterior`, `status_novo`, `alterado_em`), em ordem cronológica.

> A Fase 1 não registra mudanças de status — a ferramenta `atualizar_status` só existe na
> Fase 3. Portanto, nesta fase a lista de histórico de cada chamado vem **vazia** para todos
> os dados fictícios. Isso é o resultado correto, não uma falha: ainda não houve mudança
> alguma. O caminho de leitura fica pronto para ser exercitado de verdade na Fase 3.

**R3 — Cliente sem chamados.**
Cliente que não existe, ou que não tem chamados, retorna resultado vazio com `total = 0`,
sem erro. Distinto de erro de entrada: aqui a busca é válida e simplesmente não achou nada.

**R4 — Nome do cliente vazio é rejeitado.**
Nome vazio ou só com espaços retorna erro explicativo, já que não identifica cliente algum.

**R5 — Correspondência exata.**
A busca é por correspondência exata do nome, ignorando maiúsculas/minúsculas e espaços nas
extremidades. Busca parcial (substring) fica fora do escopo desta fase: exigiria definir
regras de relevância e ordenação que não são necessárias para o objetivo.

**R6 — Resumo do cliente.**
Além da lista, retorna um resumo com o total de chamados e a contagem por status, para que um
agente responda "quantos chamados abertos o cliente X tem?" sem percorrer a lista.

## Entradas

| Parâmetro | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `cliente` | texto | sim | Nome do cliente a consultar |

## Saídas

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `cliente` | texto | O nome consultado |
| `total` | inteiro | Quantidade de chamados encontrados |
| `resumo` | objeto | `por_status`: contagem de chamados por status |
| `chamados` | lista | Os chamados, cada um com o campo adicional `historico` |

Em caso de erro (R4), o objeto contém apenas `erro`.

## Casos relevantes

| # | Situação | Resultado esperado |
| --- | --- | --- |
| 1 | Cliente com vários chamados | Todos os chamados dele, com histórico (R1, R2) |
| 2 | Cliente com um chamado | Um item na lista (R1) |
| 3 | Cliente sem chamados | `total = 0`, lista vazia, sem erro (R3) |
| 4 | Cliente inexistente | Igual ao caso 3 (R3) |
| 5 | Nome com maiúsculas diferentes | Encontra o cliente (R5) |
| 6 | Nome com espaços nas pontas | Encontra o cliente (R5) |
| 7 | Nome vazio ou só espaços | Erro explicativo (R4) |
| 8 | Cliente com chamados em status variados | `resumo.por_status` correto (R6) |
| 9 | Regressão da Fase 1 | `listar_chamados` continua funcionando |
