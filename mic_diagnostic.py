import speech_recognition as sr
import time

print("SpeechRecognition version:", sr.__version__)

mic = sr.Microphone(device_index=13)
recognizer = sr.Recognizer()

try:
    with mic as source:
        print("1. Microphone entered")
        print("2. Stream exists:", source.stream is not None)

        print("3. Calibrating...")
        recognizer.adjust_for_ambient_noise(source, duration=2)

        print("4. Stream after calibration:", source.stream is not None)

        print("5. Testing listen...")
        audio = recognizer.listen(source, timeout=8, phrase_time_limit=5)

        print("6. Recording successful!")
        print("Audio bytes:", len(audio.get_raw_data()))

except Exception as e:
    print("TEST FAILED:", type(e).__name__, repr(e))
