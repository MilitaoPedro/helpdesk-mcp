# Roadmap

O projeto é construído em **três fases pequenas e ordenadas**. Cada fase adiciona uma
ferramenta ao servidor e é especificada em detalhe apenas quando chega a sua vez — aqui
registramos apenas o objetivo e o critério de conclusão.

A ordem importa: as duas últimas fases dependem da estrutura de banco criada na primeira.

---

## Fase 1 — `listar_chamados`

**Status:** ✅ Concluída

**Objetivo:** criar a base do servidor MCP e do banco SQLite, e expor a ferramenta
`listar_chamados`, que lista os chamados com filtro opcional por status.

**Critério de conclusão:** o servidor inicia via `stdio`, cria e popula o banco
automaticamente, e a ferramenta `listar_chamados` retorna todos os chamados quando chamada sem
filtro e apenas os do status informado quando recebe um filtro. O caso de filtro sem resultados
retorna uma lista vazia, sem erro.

---

## Fase 2 — `buscar_historico_cliente`

**Status:** ⬜ Pendente

**Objetivo:** expor a ferramenta `buscar_historico_cliente`, que retorna os chamados de um
cliente e o histórico de mudanças de status desses chamados.

**Critério de conclusão:** a ferramenta retorna todos os chamados do cliente informado e, para
cada um, as mudanças de status registradas. Cliente sem chamados retorna resultado vazio sem
erro. A ferramenta `listar_chamados` continua funcionando (teste de regressão).

---

## Fase 3 — `atualizar_status`

**Status:** ⬜ Pendente

**Objetivo:** expor a ferramenta `atualizar_status`, que altera o status de um chamado e
registra a mudança.

**Critério de conclusão:** a ferramenta altera o status, persiste a mudança no banco e registra
o evento em `historico_status` **preservando o histórico anterior**. Status inválido e
identificador inexistente são rejeitados com mensagem clara, sem alterar o banco. As duas
ferramentas anteriores continuam funcionando.

---

## Depois das três fases

Com o servidor completo, a **Parte 2** do trabalho adiciona um protótipo de interface em
Streamlit que conversa com o servidor através de um client MCP, em uma pasta separada (`app/`).
Essa etapa não usa Spec-Driven Development por ser um protótipo de interface.

---

# Registro de replanejamento

## Replanejamento 1 — após a Fase 1

**Pergunta 1: a estrutura do banco suporta as duas fases seguintes?**

Sim, sem alterações. A tabela `historico_status` já foi criada na Fase 1, embora só passe a
ser escrita na Fase 3. Criá-la junto com `chamados` evita uma migração de esquema depois — o
custo foi uma tabela vazia por duas fases. Como a Fase 2 precisa ler esse histórico e a Fase 3
precisa escrevê-lo, a alternativa seria alterar o esquema no meio do projeto, com risco de
perder dados de um banco já em uso.

**Pergunta 2: alguma regra nova precisa entrar na constituição?**

Sim, duas, ambas já refletidas em `specs/pilha-tecnologia.md` durante a Fase 1:

1. **Status inválido é erro explícito, não lista vazia.** Decidido ao especificar a Fase 1.
   Vale para as três fases: um filtro ou status inválido devolve uma mensagem com os valores
   aceitos, para não ser confundido com "não há resultados".
2. **Caminho do banco é resolvido na chamada, não como valor padrão de argumento.** Descoberto
   na implementação: valores padrão em Python são avaliados uma única vez, na definição da
   função, o que fez os primeiros testes escreverem no banco real em vez de um temporário. A
   correção (resolver o caminho dentro da função) precisa ser mantida nas próximas fases.

**Pergunta 3: os critérios das fases restantes continuam adequados?**

Sim, com um acréscimo. Os critérios das Fases 2 e 3 já previam testes de regressão das
ferramentas anteriores. Acrescenta-se que a Fase 2 deve exibir, junto de cada chamado, o
histórico de mudanças — e não apenas listar os chamados do cliente, que seria redundante com
`listar_chamados`.

**Pergunta 4: algo a dividir, esclarecer ou remover?**

Nada a remover. Esclarece-se um ponto para a Fase 3: `atualizar_status` deve rejeitar a
mudança para um status **igual ao atual** ou registrá-la? Decisão: registrar apenas quando o
status realmente muda, evitando poluir o histórico com eventos sem efeito. A regra fica
detalhada na especificação da Fase 3.
