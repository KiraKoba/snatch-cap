import streamlit as st
import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
import os
import tempfile

# === CONFIGURAÇÕES DA APLICAÇÃO ===
st.set_page_config(page_title="Transcritor de Áudio com Whisper", layout="centered")

# --- Variáveis de Configuração ---
DEFAULT_DURATION = 5  # Duração padrão da gravação em segundos
SAMPLE_RATE = 48000
CHANNELS = 2
MODEL_SIZE = "small"

# === INICIALIZAÇÃO DO ESTADO DA SESSÃO ===
# Mantém o histórico da transcrição entre as interações
if 'transcricao_historico' not in st.session_state:
    st.session_state.transcricao_historico = ""
if 'recording' not in st.session_state:
    st.session_state.recording = False

# === FUNÇÕES DE APOIO ===

@st.cache_resource
def carregar_modelo_whisper():
    """Carrega o modelo Whisper apenas uma vez para toda a aplicação."""
    st.info("🔁 Carregando modelo Whisper... Aguarde um momento.")
    try:
        model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        st.success("✅ Modelo carregado com sucesso!")
        return model
    except Exception as e:
        st.error(f"❌ Erro ao carregar o modelo: {e}")
        st.stop()
        return None

def obter_dispositivos():
    """Retorna uma lista de dispositivos de entrada de áudio disponíveis."""
    try:
        devices = sd.query_devices()
        input_devices = [
            dev for dev in devices if dev['max_input_channels'] >= CHANNELS
        ]
        return input_devices
    except Exception as e:
        st.error(f"❌ Erro ao listar dispositivos de áudio: {e}")
        return []

def gravar_audio(duracao, device_index):
    """Grava áudio do dispositivo selecionado."""
    st.info(f"🎧 Gravando {duracao} segundos...")
    try:
        audio = sd.rec(
            int(duracao * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='int16',
            device=device_index
        )
        sd.wait()
        st.success("✅ Gravação concluída!")
        return audio
    except Exception as e:
        st.error(f"❌ Erro durante a gravação: {e}")
        return None

def transcrever_audio(caminho_audio):
    """Transcreve o arquivo de áudio usando o modelo Whisper."""
    model = st.session_state.model
    st.info("🧠 Transcrevendo...")
    try:
        segments, _ = model.transcribe(caminho_audio, beam_size=5)
        transcricao_atual = " ".join([segment.text for segment in segments])
        st.session_state.transcricao_historico += transcricao_atual + " "
        st.success("✅ Transcrição concluída!")
        return transcricao_atual
    except Exception as e:
        st.error(f"❌ Erro na transcrição: {e}")
        return ""

# === INTERFACE DO STREAMLIT ===

st.title("🗣️ Transcritor de Fala")
st.markdown("Clique em **Gravar e Transcrever** para iniciar uma nova gravação e ver a transcrição.")

# --- Barra lateral para seleção do dispositivo ---
with st.sidebar:
    st.header("⚙️ Configurações")
    dispositivos = obter_dispositivos()
    if not dispositivos:
        st.warning("Nenhum dispositivo de entrada de áudio válido encontrado.")
        st.stop()

    dispositivo_nomes = [f"{dev['name']} ({dev['index']})" for dev in dispositivos]
    dispositivo_selecionado_str = st.selectbox(
        "Selecione o dispositivo de entrada:",
        dispositivo_nomes
    )
    # Extrai o índice do dispositivo
    device_index = int(dispositivo_selecionado_str.split('(')[-1].replace(')', ''))
    
    st.write(f"Você selecionou o dispositivo: {dispositivos[device_index]['name']}")
    
    # Adiciona um slider para a duração da gravação
    duracao_gravação = st.slider(
        "Duração da gravação (segundos):",
        min_value=1,
        max_value=30,
        value=DEFAULT_DURATION
    )

# === LÓGICA DE EXECUÇÃO ===

# Carrega o modelo na primeira vez que o script é executado
if 'model' not in st.session_state:
    st.session_state.model = carregar_modelo_whisper()

# Botão para iniciar a gravação
if st.button("Gravar e Transcrever", use_container_width=True, type="primary"):
    st.session_state.recording = True
    
    # Usa um arquivo temporário para salvar o áudio
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio_file:
        audio_path = tmp_audio_file.name

    # Grava o áudio
    audio_data = gravar_audio(duracao_gravação, device_index)
    if audio_data is not None:
        try:
            write(audio_path, SAMPLE_RATE, audio_data)
        except Exception as e:
            st.error(f"❌ Erro ao salvar o arquivo de áudio: {e}")
            st.stop()
    
        # Transcreve o áudio e atualiza o estado
        with st.spinner('Aguardando a transcrição...'):
            transcricao_atual = transcrever_audio(audio_path)
            
        # Exibe a transcrição atual e o histórico
        st.markdown("---")
        st.subheader("Transcrição Atual:")
        st.write(transcricao_atual)
    
        # Limpa o arquivo temporário
        os.remove(audio_path)
    
    st.session_state.recording = False

# --- Exibe o histórico de transcrição ---
st.markdown("---")
st.subheader("Histórico Completo da Transcrição")
if st.session_state.transcricao_historico:
    st.markdown(st.session_state.transcricao_historico)
else:
    st.info("Nenhuma transcrição ainda. Clique no botão para começar.")
