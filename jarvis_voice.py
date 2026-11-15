
"""
jarvis_voice.py - Windows Jarvis Voice Assistant
Continuous microphone listening and speech recognition.
"""

import time
import speech_recognition as sr
import jarvis_brain

# Microphone device that previously captured nonzero audio
MICROPHONE_INDEX = 1


def speak(text):
    if not text:
        return

    print(f"\n[JARVIS]: {text}\n")

    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        engine.say(str(text))
        engine.runAndWait()
        engine.stop()

    except Exception as e:
        print("Voice output error:", e)


def text_mode():
    print("Jarvis text mode activated.")

    while True:
        try:
            query = input("\nYou: ").strip()

            if query.lower() in ["exit", "quit", "stop jarvis"]:
                print("Jarvis shutting down.")
                break

            if query:
                response = jarvis_brain.think(query)
                speak(response)

        except KeyboardInterrupt:
            print("\nJarvis shutting down.")
            break

        except Exception as e:
            print("Error:", e)


def listen_loop():

    recognizer = sr.Recognizer()

    # Microphone listening settings
    recognizer.energy_threshold = 35
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.0
    recognizer.non_speaking_duration = 0.5

    print("Checking microphone...")

    try:
        mic = sr.Microphone(device_index=MICROPHONE_INDEX)

        print("\n" + "=" * 45)
        print("          JARVIS IS READY")
        print("=" * 45)
        print("Speak clearly into your microphone.")
        print("Say: Jarvis, open Spotify")
        print("Say: Jarvis, play Dynamite on Spotify")
        print("Say: Jarvis, open YouTube")
        print("Say: Jarvis, open WhatsApp")
        print("Say: Jarvis, stock market update")
        print("Say: exit to stop Jarvis")
        print("=" * 45)

        # Keep microphone active throughout listening
        with mic as source:

            print("\nMicrophone connected successfully.")

            print("Calibrating microphone. Please remain quiet...")
            recognizer.adjust_for_ambient_noise(
                source,
                duration=2
            )

            print(
                "Microphone calibrated. Energy threshold:",
                recognizer.energy_threshold
            )

            while True:

                try:
                    print("\nListening... Speak now!")

                    # Wait indefinitely until speech begins
                    audio = recognizer.listen(
                        source,
                        timeout=None,
                        phrase_time_limit=10
                    )

                    print("Recognizing your voice...")

                    query = recognizer.recognize_google(
                        audio,
                        language="en-IN"
                    ).strip()

                    print("You said:", query)

                    q_clean = query.lower().strip()

                    # Exit command
                    if q_clean in ["exit", "quit", "stop jarvis"]:
                        speak("Goodbye!")
                        break

                    # Remove wake word
                    if q_clean.startswith("jarvis"):
                        q_clean = q_clean[len("jarvis"):].strip(
                            " ,.!?"
                        )

                    if not q_clean:
                        speak("Yes, I'm listening.")
                        continue

                    print("Processing your command...")

                    response = jarvis_brain.think(q_clean)

                    speak(response)

                except sr.UnknownValueError:
                    print(
                        "I heard something, but couldn't understand it. "
                        "Please repeat."
                    )

                except sr.RequestError as e:
                    print("Speech recognition network error:", e)
                    time.sleep(2)

                except KeyboardInterrupt:
                    print("\nJarvis shutting down. Goodbye!")
                    return

                except Exception as e:
                    print("Unexpected error:", repr(e))
                    time.sleep(1)

    except KeyboardInterrupt:
        print("\nJarvis shutting down. Goodbye!")

    except Exception as e:
        print("\nMicrophone initialization error:", repr(e))
        print("Voice mode could not start.")
        print("Check your microphone connection and device index.")


if __name__ == "__main__":
    listen_loop()
