# Fase 3 — `atualizar_status`: requisitos

## Objetivo

Expor a ferramenta `atualizar_status`, que muda o status de um chamado e registra a mudança no
histórico — a única operação de escrita do projeto.

## Comportamentos

**R1 — Atualizar o status.**
Altera o status do chamado identificado e persiste a mudança no banco.

**R2 — Registrar a mudança no histórico.**
Cada mudança efetiva insere um registro em `historico_status` com o status anterior, o novo e
o momento da alteração. O histórico **acumula**: mudanças anteriores nunca são apagadas nem
sobrescritas.

**R3 — Atualizar o carimbo de tempo.**
`atualizado_em` passa a refletir o momento da última alteração. `criado_em` **não** muda: é o
registro de quando o chamado foi aberto, e reescrevê-lo destruiria informação.

**R4 — Status inválido é rejeitado.**
Status fora de `aberto`/`em_andamento`/`fechado` retorna erro com os valores aceitos, sem
alterar o banco.

**R5 — Chamado inexistente é rejeitado.**
Identificador que não corresponde a nenhum chamado retorna erro, sem alterar o banco e sem
criar registro de histórico órfão.

**R6 — Mudança para o mesmo status não é registrada.**
Se o novo status for igual ao atual, nada muda: nem o `atualizado_em`, nem o histórico. A
resposta informa que nenhuma alteração foi necessária.

> Decisão do Replanejamento 1. Registrar eventos sem efeito poluiria o histórico e faria um
> atendente achar que houve mudança onde não houve. A resposta distingue os dois casos para
> que o agente possa dizer "já estava nesse status" em vez de "atualizei".

**R7 — Erros não deixam o banco pela metade.**
Qualquer rejeição (R4–R6) deixa o banco exatamente como estava: nem status alterado, nem
histórico registrado.

## Entradas

| Parâmetro | Tipo | Obrigatório | Descrição |
| --- | --- | --- | --- |
| `chamado_id` | inteiro | sim | Identificador do chamado |
| `novo_status` | texto | sim | O novo status |

## Saídas

**Sucesso (houve mudança):**

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `atualizado` | booleano | `true` |
| `chamado_id` | inteiro | O chamado alterado |
| `status_anterior` | texto | Status antes da mudança |
| `status_novo` | texto | Status depois da mudança |
| `mensagem` | texto | Descrição legível do que aconteceu |

**Sem mudança (R6):** `atualizado = false`, com `status_anterior` e `status_novo` iguais.

**Erro (R4, R5):** `erro` e, quando aplicável, `status_validos`.

## Casos relevantes

| # | Situação | Resultado esperado |
| --- | --- | --- |
| 1 | `aberto` → `em_andamento` | Status muda e histórico registra (R1, R2) |
| 2 | `em_andamento` → `fechado` | Status muda e histórico registra (R1, R2) |
| 3 | Mudança persiste | Nova consulta ao banco mostra o novo status (R1) |
| 4 | `atualizado_em` muda | Carimbo de tempo atualizado (R3) |
| 5 | `criado_em` não muda | Data de abertura preservada (R3) |
| 6 | Mudanças sucessivas | Histórico acumula, nada é perdido (R2) |
| 7 | Status inválido | Erro, banco intacto (R4) |
| 8 | Chamado inexistente | Erro, banco intacto (R5) |
| 9 | Status igual ao atual | Sem mudança, sem registro (R6) |
| 10 | Regressão das Fases 1 e 2 | As duas ferramentas anteriores seguem funcionando |
| 11 | Histórico na Fase 2 | `buscar_historico_cliente` passa a exibir as mudanças |
