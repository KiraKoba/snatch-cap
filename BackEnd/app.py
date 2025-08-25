# app.py
import streamlit as st
from transcricao_lib import Transcritor
import sounddevice as sd # Importado para listar os devices

# === CONFIGURAÇÕES GERAIS DA APLICAÇÃO ===
SAMPLE_RATE = 16000 # Whisper funciona melhor com 16kHz
CHANNELS = 1 # Mono é suficiente para transcrição

# --- Funções Auxiliares ---

@st.cache_resource
def carregar_transcritor():
    """
    Carrega a classe Transcritor e a mantém em cache para não recarregar
    o modelo a cada interação na UI.
    """
    return Transcritor(model_size="small")

def encontrar_devices_validos(canais):
    """
    Encontra dispositivos de entrada de áudio válidos.
    """
    devices = sd.query_devices()
    devices_validos = {}
    for i, dev_info in enumerate(devices):
        # Verifica se o dispositivo tem canais de entrada
        if dev_info['max_input_channels'] >= canais:
            devices_validos[dev_info['name']] = i
    return devices_validos

# --- INTERFACE STREAMLIT ---

st.set_page_config(layout="wide", page_title="Transcrição de Áudio Inteligente")

st.title("🎙️ Transcrição Inteligente com Detecção de Fala")
st.markdown("""
Esta aplicação ouve o microfone continuamente. Quando você fala e faz uma pausa,
ela transcreve a frase completa, evitando cortes.
""")

st.info("""
**Novas dependências necessárias!** Para a detecção de fala, instale:
`pip install pyaudio webrtcvad-wheels`
""", icon="ℹ️")


# Carrega o modelo (usando o cache do Streamlit)
transcritor = carregar_transcritor()

# Inicializa o estado da sessão
if 'rodando' not in st.session_state:
    st.session_state.rodando = False
if 'texto_completo' not in st.session_state:
    st.session_state.texto_completo = ""
if 'device_selecionado' not in st.session_state:
    st.session_state.device_selecionado = None


# --- Seleção de Dispositivo ---
st.sidebar.header("Configurações de Áudio")
devices_disponiveis = encontrar_devices_validos(CHANNELS)


if not devices_disponiveis:
    st.error("❌ Nenhum dispositivo de gravação válido foi encontrado. Verifique as permissões do microfone e se ele está conectado.")
else:
    # Dropdown para selecionar o dispositivo
    nome_device_selecionado = st.sidebar.selectbox(
        "Selecione o dispositivo de áudio (microfone):",
        options=list(devices_disponiveis.keys())
    )
    st.session_state.device_selecionado = devices_disponiveis[nome_device_selecionado]
    st.sidebar.info(f"Dispositivo selecionado: `{nome_device_selecionado}` (Índice: {st.session_state.device_selecionado})")

    # --- Controles da Aplicação ---
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("▶️ Iniciar Transcrição", type="primary", disabled=st.session_state.rodando, use_container_width=True):
            st.session_state.rodando = True
            st.rerun()

    with col2:
        if st.button("⏹️ Parar Transcrição", disabled=not st.session_state.rodando, use_container_width=True):
            st.session_state.rodando = False
            st.rerun()
    
    with col3:
        if st.button("🧹 Limpar Histórico", use_container_width=True):
            st.session_state.texto_completo = ""
            st.rerun()


    # --- Lógica de Gravação e Transcrição ---
    if st.session_state.rodando:
        st.info("Ouvindo... Fale no microfone. A transcrição aparecerá após uma pausa.")
        
        placeholder_texto = st.empty()
        
        while st.session_state.rodando:
            # CORREÇÃO: Passando o estado 'rodando' como argumento para a função
            caminho_audio = transcritor.gravar_com_vad(
                device_index=st.session_state.device_selecionado,
                rodando_state=st.session_state.rodando
            )

            # Se o botão de parar for pressionado durante a gravação, o loop principal vai parar
            if not st.session_state.rodando:
                break

            if caminho_audio:
                texto_chunk = transcritor.transcrever_audio(caminho_audio)
                if texto_chunk:
                    st.session_state.texto_completo += texto_chunk + " "

            with placeholder_texto.container():
                st.subheader("Texto Transcrito:")
                st.text_area(
                    "Transcrição",
                    value=st.session_state.texto_completo,
                    height=300,
                    label_visibility="collapsed"
                )
    else:
        st.warning("A transcrição está parada. Pressione 'Iniciar' para começar.")


# Exibe o texto final mesmo quando parado, para facilitar a cópia
if st.session_state.texto_completo:
    st.subheader("Transcrição Completa:")
    st.text_area("Você pode copiar o texto final daqui:", st.session_state.texto_completo, height=250, key="final_text_area")
