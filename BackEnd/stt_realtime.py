import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
import os

# === CONFIGURAÇÕES GERAIS ===
DURATION = 3  # Grava apenas 3s para teste
SAMPLE_RATE = 48000
CHANNELS = 2
MODEL_SIZE = "small"

# Caminho da pasta onde está o script atual
PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__))

# === INICIALIZA O MODELO ===
print("🔁 Carregando modelo Whisper...")
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

def tentar_gravar_com_device(index):
    print(f"🎧 Testando device {index}...")
    try:
        audio = sd.rec(
            int(DURATION * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='int16',
            device=index
        )
        sd.wait()
        # Nome do arquivo WAV: "audio_device_{index}.wav" na pasta atual
        nome_arquivo_wav = os.path.join(PASTA_ATUAL, f"audio_device_{index}.wav")
        write(nome_arquivo_wav, SAMPLE_RATE, audio)
        return nome_arquivo_wav
    except Exception as e:
        print(f"❌ Falhou no device {index}: {e}")
        return None

def transcrever_audio(caminho):
    print("🧠 Transcrevendo...")
    segments, _ = model.transcribe(caminho, beam_size=5)
    texto_final = ""
    for segment in segments:
        print(f"[{segment.start:.2f}s - {segment.end:.2f}s]: {segment.text}")
        texto_final += segment.text + " "

    # Salvar a transcrição acumulada em um arquivo fixo
    arquivo_txt = os.path.join(PASTA_ATUAL, "transcricao_completa.txt")
    with open(arquivo_txt, "a", encoding="utf-8") as f:  # modo append 'a'
        f.write(texto_final + "\n")

    print(f"📝 Transcrição atual adicionada em: {arquivo_txt}")
    return texto_final

# === TENTAR TODOS OS DEVICES ===
def encontrar_device_funcional():
    print("\n🔍 Procurando um dispositivo funcional...\n")
    for device_index in range(len(sd.query_devices())):
        dev_info = sd.query_devices(device_index)
        if dev_info['max_input_channels'] >= CHANNELS:
            caminho = tentar_gravar_com_device(device_index)
            if caminho:
                print(f"\n✅ FUNCIONOU! Usando device {device_index}: {dev_info['name']}\n")
                return device_index
    return None

# === EXECUÇÃO PRINCIPAL ===
DEVICE_INDEX = encontrar_device_funcional()
if DEVICE_INDEX is None:
    print("❌ Nenhum dispositivo de gravação válido encontrado.")
    exit()

print("🔁 Iniciando loop de gravação e transcrição...\n")
try:
    while True:
        caminho_audio = tentar_gravar_com_device(DEVICE_INDEX)
        if caminho_audio:
            transcrever_audio(caminho_audio)
            # Opcional: remover o arquivo WAV se quiser economizar espaço
            # os.remove(caminho_audio)
except KeyboardInterrupt:
    print("\n❌ Encerrado pelo usuário.")
