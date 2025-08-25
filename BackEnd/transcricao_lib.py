# transcricao_lib.py
import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
import os
import tempfile
import pyaudio
import webrtcvad
import collections
import wave

class Transcritor:
    """
    Classe para encapsular a lógica de gravação e transcrição de áudio.
    Agora com suporte a Detecção de Atividade de Voz (VAD).
    """
    def __init__(self, model_size="small"):
        """
        Inicializa o modelo Whisper.
        """
        print("🔁 Carregando modelo Whisper...")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print("✅ Modelo carregado.")
        self.temp_dir = tempfile.gettempdir()

    def listar_devices(self):
        """
        Lista todos os dispositivos de áudio disponíveis.
        """
        return sd.query_devices()

    # CORREÇÃO: Adicionado o parâmetro 'rodando_state'
    def gravar_com_vad(self, device_index, rodando_state, sample_rate=16000, chunk_duration_ms=30, vad_aggressiveness=3, padding_duration_ms=300, silence_timeout_s=1.5):
        """
        Grava áudio do microfone usando Voice Activity Detection (VAD).
        Para de gravar após um período de silêncio e retorna o caminho do arquivo de áudio.
        O loop é controlado pelo parâmetro 'rodando_state'.
        """
        p = pyaudio.PyAudio()
        vad = webrtcvad.Vad(vad_aggressiveness)

        frames_per_chunk = int(sample_rate * chunk_duration_ms / 1000)
        padding_frames = int(padding_duration_ms / chunk_duration_ms)
        
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=sample_rate,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=frames_per_chunk)

        print("🎤 Ouvindo... Fale alguma coisa.")
        
        ring_buffer = collections.deque(maxlen=padding_frames)
        triggered = False
        voiced_frames = []
        silent_chunks = 0
        max_silent_chunks = int(silence_timeout_s * 1000 / chunk_duration_ms)

        # CORREÇÃO: O loop agora verifica o parâmetro 'rodando_state'
        while rodando_state:
            try:
                frame = stream.read(frames_per_chunk, exception_on_overflow=False)
                is_speech = vad.is_speech(frame, sample_rate)

                if not triggered:
                    ring_buffer.append((frame, is_speech))
                    if any(f[1] for f in ring_buffer):
                        triggered = True
                        print("🗣️ Fala detectada, gravando...")
                        voiced_frames.extend(f[0] for f in ring_buffer)
                        ring_buffer.clear()
                else:
                    voiced_frames.append(frame)
                    if not is_speech:
                        silent_chunks += 1
                        if silent_chunks > max_silent_chunks:
                            print(f"🤫 Silêncio detectado por mais de {silence_timeout_s}s. Processando...")
                            break # Sai do loop de gravação para processar o áudio
                    else:
                        silent_chunks = 0
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Erro durante a gravação: {e}")
                break
        
        stream.stop_stream()
        stream.close()
        p.terminate()

        if voiced_frames:
            temp_wav_path = os.path.join(self.temp_dir, "vad_chunk.wav")
            with wave.open(temp_wav_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(sample_rate)
                wf.writeframes(b''.join(voiced_frames))
            
            print(f"✅ Áudio da fala salvo em: {temp_wav_path}")
            return temp_wav_path
        else:
            return None


    def transcrever_audio(self, caminho_arquivo):
        """
        Transcreve um arquivo de áudio usando o modelo Whisper.
        """
        if not caminho_arquivo or not os.path.exists(caminho_arquivo):
            return ""

        print(f"🧠 Transcrevendo o arquivo: {caminho_arquivo}...")
        try:
            segments, _ = self.model.transcribe(caminho_arquivo, beam_size=5, language="pt")
            texto_transcrito = " ".join(segment.text for segment in segments)
            print(f"📝 Texto: {texto_transcrito}")
            return texto_transcrito.strip()
        except Exception as e:
            print(f"❌ Erro na transcrição: {e}")
            return ""
        finally:
            if os.path.exists(caminho_arquivo):
                try:
                    os.remove(caminho_arquivo)
                except OSError as e:
                    print(f"Erro ao remover o arquivo {caminho_arquivo}: {e}")
