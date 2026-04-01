"""
Interface Streamlit para o Banco Ágil.

Fornece uma interface de chat para interação com o sistema
multi-agentes de atendimento bancário.
"""

import asyncio
import os
import re
import uuid
import logging

# Configura logging em arquivo para debug
logging.basicConfig(
    filename='debug_agentes.log',
    level=logging.DEBUG,
    format='%(asctime)s | %(message)s',
    datefmt='%H:%M:%S',
    force=True,
)
log = logging.getLogger("banco_agil_debug")

import streamlit as st
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.adk.sessions import Session
from google.genai import types

from banco_agil.agentes.triagem import root_agent

# Carrega variáveis de ambiente (.env)
load_dotenv()


# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Banco Ágil — Atendimento",
    page_icon="🏦",
    layout="centered",
)


# ---------------------------------------------------------------------------
# Estilização customizada (Premium UI & Dark Mode Aware)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    .header-container {
        text-align: center;
        padding: 2rem 0 1rem 0;
        background: linear-gradient(135deg, #1A4B84 0%, #2A75C9 100%);
        border-radius: 0 0 20px 20px;
        margin-top: -4rem; /* Força colar no teto do streamlit */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    .header-container h1 {
        color: #FFFFFF;
        font-size: 2.2rem;
        font-weight: 600;
        margin-bottom: 0.2rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    .header-container p {
        color: #E8F0FE;
        font-size: 1rem;
        font-weight: 400;
        opacity: 0.9;
    }
    
    .stChatMessage {
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        background-color: var(--secondary-background-color);
        border: 1px solid var(--faded-text-color);
    }
    
    [data-testid="stSidebar"] {
        background-color: var(--secondary-background-color);
        border-right: 1px solid var(--faded-text-color);
    }
    
    /* Botão de Limpar Sessão */
    .stButton>button {
        background-color: #1A4B84;
        color: white;
        border-radius: 8px;
        transition: all 0.2s;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2A75C9;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------
st.markdown("""
<div class="header-container">
    <h1>🏦 Banco Ágil</h1>
    <p>Atendimento inteligente ao cliente</p>
</div>
""", unsafe_allow_html=True)

st.divider()


# ---------------------------------------------------------------------------
# Inicialização do estado da sessão
# ---------------------------------------------------------------------------
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

if "runner" not in st.session_state:
    st.session_state.runner = InMemoryRunner(
        agent=root_agent,
        app_name="banco_agil",
    )

if "session_id" not in st.session_state:
    # Cria uma sessão nova para o atendimento
    st.session_state.session_id = "atendimento_001"

if "user_id" not in st.session_state:
    st.session_state.user_id = "cliente_web"

if "cliente_autenticado" not in st.session_state:
    st.session_state.cliente_autenticado = False

if "atendimento_encerrado" not in st.session_state:
    st.session_state.atendimento_encerrado = False

# ---------------------------------------------------------------------------
# Função para enviar mensagem ao agente
# ---------------------------------------------------------------------------
async def enviar_mensagem(texto_usuario: str) -> str:
    """Envia uma mensagem ao agente e retorna a resposta consolidada."""
    runner = st.session_state.runner
    user_id = st.session_state.user_id
    session_id = st.session_state.session_id

    # Garante que a sessão exista
    session = await runner.session_service.get_session(
        app_name=runner.app_name,
        user_id=user_id,
        session_id=session_id,
    )
    if not session:
        await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id=user_id,
            session_id=session_id,
        )

    # Monta o conteúdo da mensagem do usuário
    conteudo = types.Content(
        role="user",
        parts=[types.Part.from_text(text=texto_usuario)],
    )

    # Coleta todas as partes da resposta do agente
    partes_resposta = []

    try:
        log.info(f"{'='*60}")
        log.info(f"Mensagem do usuário: {texto_usuario[:80]}")
        log.info(f"{'='*60}")
        
        async for evento in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=conteudo,
        ):
            # Log detalhado de cada evento
            author = getattr(evento, 'author', 'desconhecido')
            has_content = bool(evento.content and evento.content.parts)
            
            if has_content:
                for parte in evento.content.parts:
                    # Verifica se é function_call ou texto
                    is_function_call = hasattr(parte, 'function_call') and parte.function_call
                    is_function_response = hasattr(parte, 'function_response') and parte.function_response
                    
                    if is_function_call:
                        log.info(f"  Autor: {author} | FUNCTION_CALL: {parte.function_call.name}")
                        if parte.function_call.name == "encerrar_atendimento":
                            st.session_state.atendimento_encerrado = True
                    elif is_function_response:
                        log.info(f"  Autor: {author} | FUNCTION_RESPONSE")
                    elif parte.text and parte.text.strip():
                        texto_preview = parte.text.strip()[:100]
                        log.info(f"  Autor: {author} | TEXTO: {texto_preview}")
                        partes_resposta.append(parte.text)
            else:
                log.info(f"  Autor: {author} | (evento sem conteúdo)")
        
        log.info(f"Total de partes de texto coletadas: {len(partes_resposta)}")

        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return (
            "Peço desculpas, mas ocorreu uma instabilidade momentânea no nosso "
            "atendimento. Por favor, tente enviar sua mensagem novamente."
        )

    # Junta tudo numa resposta coerente
    # Fallback Anti-Vazio (Bug de reentrada ADK)
    if not partes_resposta:
        log.warning("Resposta vazia (0 tokens) detectada do ADK. Engatilhando retry forçado...")
        try:
            async for evento in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(
                    role="user", 
                    parts=[types.Part.from_text(text="[SISTEMA: A sessão foi recuperada. Por favor, reconsidere a solicitação anterior baseada no histórico da conversa e responda OBRIGATORIAMENTE em texto detalhado, chamando a ferramenta se necessário.]")]
                ),
            ):
                if evento.content and evento.content.parts:
                    for parte in evento.content.parts:
                        if parte.text and parte.text.strip():
                            partes_resposta.append(parte.text)
        except Exception as retry_e:
            log.error(f"Erro no retry anti-vazio: {retry_e}")

    if partes_resposta:
        resposta_final = "\n".join(partes_resposta)
        
        # Sanitiza: remove vazamentos de código/tool calls
        resposta_final = _sanitizar_resposta(resposta_final)
        
        # Detecta autenticação bem-sucedida de forma flexível
        resposta_lower = resposta_final.lower()
        if not st.session_state.cliente_autenticado:
            if any(termo in resposta_lower for termo in [
                "autenticação concluída", "autenticado com sucesso",
                "autenticação confirmada", "tudo certo,", "bem-vind",
            ]):
                st.session_state.cliente_autenticado = True
            
        return resposta_final

    log.error("FALHA CRÍTICA: Retry anti-vazio também falhou. Exibindo mensagem de erro padrão.")
    return (
        "No momento, enfrentamos uma ligeira instabilidade ao processar sua solicitação. "
        "Poderia repetir ou detalhar um pouco mais como posso ajudá-lo?"
    )


def _sanitizar_resposta(texto: str) -> str:
    """Remove vazamentos de código/tool calls da resposta antes de exibir."""
    # Remove chamadas de função Python que vazaram (multi-linha)
    texto = re.sub(r'print\(.*?\)', '', texto, flags=re.DOTALL)
    texto = re.sub(r'default_api\.\w+\(.*?\)', '', texto, flags=re.DOTALL)
    # Remove blocos de código markdown
    texto = re.sub(r'```.*?```', '', texto, flags=re.DOTALL)
    # Remove linhas que parecem código Python (import, def, class)
    texto = re.sub(r'^\s*(import |from |def |class ).*$', '', texto, flags=re.MULTILINE)
    # Remove parênteses/colchetes solitários que sobram após a limpeza
    texto = re.sub(r'^\s*[)\]}\>]+\s*$', '', texto, flags=re.MULTILINE)
    # Escapa $ para evitar interpretação LaTeX no Streamlit
    texto = texto.replace("R$", "R\\$")
    # Remove linhas vazias extras resultantes da limpeza
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto.strip()


def processar_mensagem(texto: str) -> str:
    """Wrapper síncrono para enviar_mensagem."""
    return asyncio.run(enviar_mensagem(texto))


# ---------------------------------------------------------------------------
# Exibe histórico de mensagens
# ---------------------------------------------------------------------------
for msg in st.session_state.mensagens:
    icone = "🙋" if msg["role"] == "user" else "🏦"
    with st.chat_message(msg["role"], avatar=icone):
        st.markdown(msg["content"])


# ---------------------------------------------------------------------------
# Input do usuário (Com Trava Condicional Sistêmica)
# ---------------------------------------------------------------------------
if st.session_state.get("atendimento_encerrado", False):
    st.info("🔒 **Atendimento encerrado.** Clique em **'Novo Atendimento'** na barra lateral para recomeçar.")
else:
    prompt = st.chat_input("Digite sua mensagem...")

    if prompt:
        # Exibe a mensagem do usuário
        st.session_state.mensagens.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🙋"):
            st.markdown(prompt)

        # Processa e exibe a resposta do agente
        with st.chat_message("assistant", avatar="🏦"):
            with st.spinner("Processando..."):
                resposta = processar_mensagem(prompt)
            st.markdown(resposta)

        st.session_state.mensagens.append({"role": "assistant", "content": resposta})
        
        # Se após processar a mensagem, o agente bloqueou a sessão, re-renderiza a tela para sumir o input instantaneamente:
        if st.session_state.get("atendimento_encerrado", False):
            st.rerun()


# ---------------------------------------------------------------------------
# Sidebar com informações
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ℹ️ Sobre")
    st.markdown(
        "O **Banco Ágil** é um banco digital premium com atendimento "
        "realizado por agentes de Inteligência Artificial."
    )
    st.markdown("---")
    
    if st.session_state.cliente_autenticado:
        st.success("✅ **Status:** Cliente Autenticado")
    else:
        st.warning("🔒 **Status:** Aguardando Autenticação")
        
    st.markdown("---")
    st.markdown("### 🔧 Serviços disponíveis")
    st.markdown(
        "- 💳 Consulta de limite de crédito\n"
        "- 📈 Solicitação de aumento de limite\n"
        "- 📊 Entrevista de reavaliação de score\n"
        "- 💱 Consulta de cotação de moedas"
    )
    st.markdown("---")

    if st.button("🔄 Novo Atendimento", use_container_width=True):
        st.session_state.mensagens = []
        st.session_state.cliente_autenticado = False
        st.session_state.atendimento_encerrado = False
        st.session_state.session_id = f"atendimento_{uuid.uuid4().hex[:8]}"
        # Reseta bloqueios de segurança de CPFs
        from banco_agil.ferramentas.autenticacao import _tentativas_falhas
        _tentativas_falhas.clear()
        st.rerun()
