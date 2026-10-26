# Fase 3 — `atualizar_status`: validação

## 1. Testes automatizados

```bash
.venv/bin/python -m pytest tests/ -v
```

| Teste | Requisito | O que confirma |
| --- | --- | --- |
| `test_atualiza_status` | R1 | O status muda e é persistido |
| `test_persiste_apos_reconsulta` | R1 | Nova consulta ao banco mostra o novo status |
| `test_registra_historico` | R2 | Um evento é inserido com anterior/novo |
| `test_historico_acumula` | R2 | Mudanças sucessivas não apagam as anteriores |
| `test_atualiza_carimbo_de_tempo` | R3 | `atualizado_em` é atualizado |
| `test_preserva_criado_em` | R3 | `criado_em` não muda |
| `test_status_invalido` | R4 | Erro com os valores aceitos |
| `test_chamado_inexistente` | R5 | Erro, sem histórico órfão |
| `test_status_igual_nao_registra` | R6 | Sem mudança, sem registro |
| `test_rejeicoes_nao_alteram_banco` | R7 | Estado idêntico antes e depois |
| `test_regressao_listar_chamados` | R10 | Fase 1 intacta |
| `test_regressao_buscar_historico` | R10 | Fase 2 intacta |
| `test_integracao_historico_visivel` | R11 | A Fase 2 exibe a mudança feita pela Fase 3 |

## 2. Verificação do requisito mais crítico (R2 + R7)

O ponto central do trabalho é que atualizar o status **não apague o histórico**. A verificação
direta:

1. atualizar o mesmo chamado três vezes (`aberto` → `em_andamento` → `fechado` → `aberto`);
2. chamar `buscar_historico_cliente` para o dono do chamado;
3. conferir que o chamado tem **três** eventos de histórico, na ordem em que ocorreram.

```bash
.venv/bin/python -m pytest tests/test_atualizar_status.py -v
```

## 3. Verificação ponta a ponta via MCP

```bash
rm -f helpdesk.db                       # parte dos dados fictícios originais
.venv/bin/python scripts/demo_mcp.py
```

O script passa a verificar também:

1. `atualizar_status` aparece na lista de ferramentas;
2. atualizar um chamado e conferir que a resposta traz status anterior e novo;
3. reconsultar via `listar_chamados` e confirmar que a mudança persistiu;
4. atualizar para o mesmo status e conferir que nada mudou;
5. tentar status inválido e chamado inexistente, conferindo as mensagens de erro;
6. conferir o histórico via `buscar_historico_cliente` — a mudança deve aparecer lá;
7. as três ferramentas continuam respondendo ao final.

## 4. Critério de aceite

- [ ] suíte completa (Fases 1, 2 e 3) passa;
- [ ] os 11 casos de `requisitos.md` têm cobertura correspondente;
- [ ] o histórico acumula mudanças e nada é perdido;
- [ ] rejeições deixam o banco intacto;
- [ ] as três ferramentas funcionam juntas, via protocolo MCP.
