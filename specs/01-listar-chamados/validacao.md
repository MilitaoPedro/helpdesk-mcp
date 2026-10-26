# Fase 1 — `listar_chamados`: validação

Como verificar que a implementação atende a `requisitos.md`.

## 1. Testes automatizados

```bash
.venv/bin/python -m pytest tests/ -v
```

Os testes usam um banco temporário próprio, então podem rodar sem afetar o banco de
desenvolvimento.

| Teste | Requisito | O que confirma |
| --- | --- | --- |
| `test_listar_todos` | R1 | Sem filtro, retorna todos os chamados do banco |
| `test_filtrar_por_status` | R2 | Cada status retorna apenas os chamados daquele status |
| `test_filtro_sem_resultados` | R3 | Status válido sem chamados retorna lista vazia, sem erro |
| `test_status_invalido` | R4 | Status fora do conjunto retorna erro com os valores válidos |
| `test_cria_banco_quando_ausente` | R5 | Banco inexistente é criado e populado |
| `test_nao_apaga_dados_existentes` | R6 | Inicialização repetida não apaga nem duplica dados |

## 2. Verificação manual

**Inicialização idempotente:**

```bash
rm -f helpdesk.db
# iniciar o servidor uma vez, depois:
.venv/bin/python -c "from helpdesk import banco; banco.inicializar(); print(banco.listar())"
```

Contar os registros, repetir o comando e conferir que o total não mudou.

**Status inválido não derruba o servidor:** este é o ponto mais frágil da fase. Um agente pode
enviar qualquer texto como filtro; se isso lançar uma exceção, o servidor cai. A chamada com
`"abertos"` deve retornar `erro` e `status_validos`, com o processo seguindo vivo.

## 3. Validação via MCP (ponta a ponta)

A validação acima chama funções Python diretamente. Isso **não** prova que a ferramenta
funciona como ferramenta MCP: o nome exposto, o esquema dos parâmetros e a serialização da
resposta só existem no protocolo.

```bash
.venv/bin/python scripts/demo_mcp.py
```

O script conecta ao servidor por `stdio`, como faria um cliente real, e então:

1. lista as ferramentas expostas e confirma que `listar_chamados` está entre elas;
2. chama sem filtro e confere o total;
3. chama com cada status válido e confere que todos os resultados têm aquele status;
4. chama com status válido sem resultados e confere a lista vazia;
5. chama com status inválido e confere a mensagem de erro.

## 4. Critério de aceite

A fase está aceita quando:

- [ ] a suíte de testes passa;
- [ ] os 7 casos de `requisitos.md` têm cobertura correspondente;
- [ ] o script de demonstração executa os 5 passos acima com sucesso via stdio;
- [ ] nenhuma saída em `stdout` além do protocolo (o protocolo não quebra).
