import pyaudio

p = pyaudio.PyAudio()

for i in range(p.get_device_count()):
    d = p.get_device_info_by_index(i)

    if d["maxInputChannels"] <= 0:
        continue

    channels = min(2, int(d["maxInputChannels"]))
    rate = int(d["defaultSampleRate"])

    print("\nTesting:", i, "-", d["name"])

    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=rate,
            input=True,
            input_device_index=i,
            frames_per_buffer=1024
        )

        data = stream.read(2048, exception_on_overflow=False)

        print("SUCCESS - Stream opened")
        print("Audio bytes:", len(data))

        stream.stop_stream()
        stream.close()

    except Exception as e:
        print("FAILED:", str(e))

p.terminate()
