import pyaudio

p = pyaudio.PyAudio()

print("PyAudio version:", pyaudio.__version__)
print("\nINPUT DEVICES:")

for i in range(p.get_device_count()):
    d = p.get_device_info_by_index(i)
    if d["maxInputChannels"] > 0:
        print(
            "Index:", i,
            "| Name:", d["name"],
            "| Channels:", d["maxInputChannels"],
            "| Rate:", d["defaultSampleRate"]
        )

print("\nTesting microphone device 13...")

try:
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        input_device_index=13,
        frames_per_buffer=1024
    )

    print("Stream opened:", stream is not None)

    if stream:
        data = stream.read(2048, exception_on_overflow=False)
        print("Audio data received:", len(data), "bytes")
        stream.stop_stream()
        stream.close()

except Exception as e:
    print("PyAudio error:", type(e).__name__, str(e))

p.terminate()
