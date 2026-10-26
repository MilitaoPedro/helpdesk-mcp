# Roadmap

O projeto é construído em **três fases pequenas e ordenadas**. Cada fase adiciona uma
ferramenta ao servidor e é especificada em detalhe apenas quando chega a sua vez — aqui
registramos apenas o objetivo e o critério de conclusão.

A ordem importa: as duas últimas fases dependem da estrutura de banco criada na primeira.

---

## Fase 1 — `listar_chamados`

**Status:** ⬜ Pendente

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
