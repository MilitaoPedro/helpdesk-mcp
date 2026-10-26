"""Protótipo de interface de atendimento (Streamlit).

Um chat simples para o atendente consultar e atualizar chamados. O app **não**
acessa o banco diretamente: todo acesso passa pelo servidor MCP, através de
`mcp_client`.

Importante: aqui não há modelo de linguagem. O texto digitado é interpretado
por regras fixas (`comandos.py`) e convertido em chamadas de ferramenta MCP.
Ou seja, é uma interface de chat que opera MCP — não um agente conversacional.

Execução:
    streamlit run app/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Permite importar os módulos vizinhos ao rodar via `streamlit run app/app.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import atendimento  # noqa: E402
import comandos as cmds  # noqa: E402

st.set_page_config(page_title="Helpdesk MCP", page_icon="🎫", layout="wide")

st.title("🎫 Helpdesk MCP")
st.caption(
    "Protótipo de atendimento. Toda consulta e alteração passa pelo servidor MCP — "
    "o app não acessa o banco diretamente."
)

# As respostas são guardadas como markdown em session_state. Renderizar
# resultados como widgets não funcionaria: o Streamlit reexecuta o script a
# cada interação e os widgets não sobrevivem entre reruns.
if "mensagens" not in st.session_state:
    st.session_state.mensagens = [
        {"papel": "assistant", "conteudo": "Olá! Sou o protótipo de atendimento do helpdesk.\n\n" + cmds.AJUDA}
    ]

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["papel"]):
        st.markdown(mensagem["conteudo"])

if prompt := st.chat_input("Ex.: listar abertos · histórico do cliente Ana Souza"):
    st.session_state.mensagens.append({"papel": "user", "conteudo": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando o servidor MCP..."):
            resposta = atendimento.responder(prompt)
        st.markdown(resposta)

    st.session_state.mensagens.append({"papel": "assistant", "conteudo": resposta})

with st.sidebar:
    st.header("Comandos")
    st.markdown(cmds.AJUDA)
    st.divider()
    st.caption(
        "As três ferramentas MCP estão em `servidor.py`. Este app é um cliente "
        "MCP: ele conversa com o servidor por stdio."
    )
    if st.button("Limpar conversa"):
        st.session_state.mensagens = []
        st.rerun()
