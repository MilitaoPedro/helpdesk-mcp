# Fase 2 — `buscar_historico_cliente`: validação

## 1. Testes automatizados

```bash
.venv/bin/python -m pytest tests/ -v
```

| Teste | Requisito | O que confirma |
| --- | --- | --- |
| `test_retorna_chamados_do_cliente` | R1 | Retorna todos os chamados daquele cliente |
| `test_nao_inclui_chamados_de_outros_clientes` | R1 | Não vaza chamados de outros clientes |
| `test_ordenado_do_mais_recente` | R1 | Ordem consistente com `listar_chamados` |
| `test_historico_presente_em_cada_chamado` | R2 | Cada chamado traz a chave `historico` |
| `test_historico_com_mudanca_registrada` | R2 | Mudança inserida à mão aparece no resultado |
| `test_cliente_sem_chamados` | R3 | Cliente sem chamados ou inexistente → vazio, sem erro |
| `test_nome_com_maiusculas_diferentes` | R5 | Busca insensível a maiúsculas/minúsculas |
| `test_nome_com_espacos_nas_pontas` | R5 | Espaços nas pontas são ignorados |
| `test_nome_vazio` | R4 | Nome vazio ou só espaços → erro |
| `test_resumo_por_status` | R6 | Contagem por status correta |
| `test_regressao_listar_chamados` | R9 | A Fase 1 continua funcionando |

## 2. Verificação ponta a ponta via MCP

```bash
.venv/bin/python scripts/demo_mcp.py
```

O script passa a verificar também:

1. `buscar_historico_cliente` aparece na lista de ferramentas;
2. um cliente com vários chamados retorna todos eles, com o campo `historico`;
3. um cliente inexistente retorna `total = 0` sem erro;
4. nome vazio retorna `erro`;
5. `listar_chamados` continua respondendo (regressão, via protocolo).

## 3. Critério de aceite

- [ ] suíte completa (Fases 1 e 2) passa;
- [ ] os 9 casos de `requisitos.md` têm cobertura correspondente;
- [ ] o histórico é lido corretamente com pelo menos uma mudança registrada;
- [ ] `listar_chamados` segue funcionando — nenhuma regressão.
