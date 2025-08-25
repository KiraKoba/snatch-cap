import sounddevice as sd

# Lista todos os dispositivos disponíveis com índice e informações
device_list = sd.query_devices()
device_info = []

for index, device in enumerate(device_list):
    print(f"[{index}] {device['name']} - Entradas: {device['max_input_channels']} - HostAPI: {sd.query_hostapis()[device['hostapi']]['name']}")
