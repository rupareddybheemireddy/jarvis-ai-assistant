import speech_recognition as sr
import audioop

r = sr.Recognizer()
m = sr.Microphone(device_index=13)

print("Speak clearly for 5 seconds...")
with m as source:
    audio = r.record(source, duration=5)

print("Audio RMS:", audioop.rms(audio.get_raw_data(), 2))

try:
    print("Recognized:", r.recognize_google(audio, language="en-IN"))
except Exception as e:
    print("Recognition error:", type(e).__name__, str(e))
