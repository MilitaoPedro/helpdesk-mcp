# Fase 1 — `listar_chamados`: planejamento

Tarefas em ordem de execução. Cada grupo termina em um estado verificável.

## Grupo 1 — Base do banco

1. Criar o módulo de banco de dados: conexão, criação das tabelas `chamados` e
   `historico_status` (a segunda já é criada agora para não exigir migração na Fase 3).
2. Implementar a inicialização idempotente: criar as tabelas se não existirem e popular com
   dados fictícios **apenas se a tabela de chamados estiver vazia** (R5, R6).
3. Definir os status aceitos em um único lugar do código, para que as três ferramentas
   compartilhem a mesma definição.

**Verificação:** apagar o banco, rodar a inicialização e conferir que ele foi criado com os
registros; rodar de novo e conferir que nada mudou.

## Grupo 2 — Consulta

4. Implementar a função de consulta ao banco: todos os chamados, ou filtrados por status,
   ordenados do mais recente para o mais antigo.
5. Converter as linhas do banco no formato de saída definido em `requisitos.md` (R1, R2).

**Verificação:** consultar sem filtro e com cada um dos três status.

## Grupo 3 — Servidor MCP

6. Criar o servidor `FastMCP` e expor `listar_chamados` como ferramenta, com o parâmetro
   `status` opcional e a descrição que um agente lê para decidir quando usá-la.
7. Tratar o status inválido retornando o erro descrito em R4, sem lançar exceção que derrube
   o servidor.
8. Chamar a inicialização do banco na subida do servidor.
9. Garantir que nada seja escrito em `stdout` além do protocolo (nenhum `print()` de depuração).

**Verificação:** iniciar o servidor e listar as ferramentas expostas.

## Grupo 4 — Testes

10. Testes automatizados cobrindo os 7 casos relevantes de `requisitos.md`, usando um banco
    temporário por teste (sem tocar no banco de desenvolvimento).
11. Verificar que a inicialização é idempotente: rodar duas vezes não duplica registros (R6).

**Verificação:** suíte de testes passando.

## Grupo 5 — Documentação

12. Registrar no README como instalar, rodar o servidor e executar os testes.
13. Criar `.mcp.json` com a configuração de registro do servidor, apontando para o Python do
    ambiente virtual.

**Verificação:** seguir o README do zero e conseguir executar os testes.

## Grupo 6 — Validação ponta a ponta

14. Criar um script que conecta ao servidor via stdio, como um cliente faria, e chama
    `listar_chamados` nos casos principais.

**Verificação:** o script retorna os mesmos resultados dos testes — evidência de que a
ferramenta funciona através do protocolo, e não apenas como função Python.
