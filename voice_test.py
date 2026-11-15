import speech_recognition as sr
import audioop

r = sr.Recognizer()
m = sr.Microphone(device_index=1)

print("Speak clearly for 5 seconds...")

with m as source:
    audio = r.record(source, duration=5)

rms = audioop.rms(audio.get_raw_data(), 2)
print("Audio RMS:", rms)

try:
    print("Recognized:", r.recognize_google(audio, language="en-IN"))
except Exception as e:
    print("Recognition error:", type(e).__name__, str(e))
