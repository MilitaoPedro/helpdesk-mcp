# Fase 2 — `buscar_historico_cliente`: planejamento

## Grupo 1 — Consulta no banco

1. Adicionar ao módulo de banco a consulta de chamados por cliente, com correspondência
   exata e insensível a maiúsculas/minúsculas, ignorando espaços nas pontas (R5).
2. Reutilizar a ordenação já existente (mais recente primeiro), para manter consistência com
   `listar_chamados`.
3. Adicionar a consulta ao histórico de um chamado, em ordem cronológica (R2).

**Verificação:** consultar um cliente conhecido, um desconhecido e variações de maiúsculas.

## Grupo 2 — Montagem da resposta

4. Montar o resumo por status a partir dos chamados encontrados (R6).
5. Anexar a cada chamado a sua lista de histórico (R2).
6. Sem duplicar lógica: a contagem por status deve derivar da mesma lista de chamados que é
   retornada, e não de uma segunda consulta que poderia divergir dela.

**Verificação:** conferir que a soma de `resumo.por_status` bate com `total`.

## Grupo 3 — Ferramenta MCP

7. Expor `buscar_historico_cliente` no servidor, com descrição que ajude um agente a escolher
   entre esta ferramenta e `listar_chamados`.
8. Tratar nome vazio retornando erro como resultado, sem lançar exceção (R4), no mesmo padrão
   da Fase 1.

**Verificação:** a ferramenta aparece na lista e responde aos casos principais.

## Grupo 4 — Testes

9. Testes dos 9 casos relevantes, incluindo o caso "cliente sem chamados" e o nome vazio.
10. **Teste de regressão da Fase 1**: `listar_chamados` continua retornando os mesmos
    resultados depois das mudanças no módulo de banco.
11. Teste do caminho não vazio do histórico: inserir uma mudança de status à mão e conferir
    que ela aparece no resultado. Sem isso, o código de leitura do histórico passaria nesta
    fase sem nunca ter sido exercitado — só seria testado na Fase 3.

**Verificação:** suíte completa (Fases 1 e 2) passando.

## Grupo 5 — Atualização da documentação

12. Documentar a ferramenta no README, no mesmo formato de `listar_chamados`.
13. Acrescentar o passo correspondente ao script de validação por MCP.

**Verificação:** script `demo_mcp.py` cobrindo as duas ferramentas.
