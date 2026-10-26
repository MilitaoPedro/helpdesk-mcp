# Fase 3 — `atualizar_status`: planejamento

## Grupo 1 — Escrita no banco

1. Adicionar ao módulo de banco a função de atualizar o status de um chamado.
2. Fazer a operação em **transação única**: ler o status atual, atualizar `chamados` e inserir
   em `historico_status` devem ser commitados juntos ou não acontecer (R7). Sem isso, uma
   falha no meio deixaria o status alterado sem o registro correspondente — exatamente o
   histórico corrompido que a arquitetura existe para evitar.
3. Atualizar `atualizado_em` sem tocar em `criado_em` (R3).
4. Retornar informação suficiente para a ferramenta distinguir "mudou" de "não havia o que
   mudar", em vez de decidir isso fora da transação.

**Verificação:** atualizar um chamado e conferir status, carimbo de tempo e histórico; repetir
com o mesmo status e conferir que nada mudou.

## Grupo 2 — Validações

5. Validar o status contra `STATUS_VALIDOS` antes de tocar no banco (R4).
6. Validar a existência do chamado antes de escrever (R5) — a chave estrangeira impediria um
   histórico órfão, mas o erro genérico do banco não diria ao agente o que houve.
7. Comparar com o status atual e não escrever quando forem iguais (R6).

**Verificação:** cada rejeição deixa o banco idêntico ao estado anterior.

## Grupo 3 — Ferramenta MCP

8. Expor `atualizar_status`, deixando explícito na descrição que é a única ferramenta que
   **altera** dados — um agente deve saber disso antes de chamá-la.
9. Retornar erro como resultado, no mesmo padrão das fases anteriores.

**Verificação:** a ferramenta aparece na lista; os erros não derrubam o servidor.

## Grupo 4 — Testes

10. Testes dos 11 casos relevantes.
11. **Testes de regressão** das Fases 1 e 2.
12. **Teste de integração entre fases:** depois de `atualizar_status`, chamar
    `buscar_historico_cliente` e conferir que a mudança aparece no histórico. É o caso 11 e
    fecha o ciclo: a Fase 2 lê o que a Fase 3 escreve.
13. Reforçar os testes de "banco intacto" comparando o estado completo antes e depois de cada
    rejeição (R7), e não apenas o status do chamado.

**Verificação:** suíte completa (Fases 1, 2 e 3) passando.

## Grupo 5 — Documentação e validação final

14. Documentar a ferramenta no README.
15. Acrescentar ao script de validação por MCP os passos de escrita, incluindo
    reconsulta para provar persistência.
16. Marcar as três fases como concluídas no roadmap (replanejamento final).

**Verificação:** `demo_mcp.py` cobrindo as três ferramentas.
