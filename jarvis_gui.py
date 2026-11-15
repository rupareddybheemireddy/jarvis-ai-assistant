
import json
import math
import threading
import time
import webbrowser
from array import array
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import speech_recognition as sr
import jarvis_brain
import jarvis_voice


HOST = "127.0.0.1"
PORT = 8765

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "jarvis_workplace.html"

LOCK = threading.Lock()
STOP_EVENT = threading.Event()

MIC_HISTORY = deque(maxlen=300)
MIC_TOTAL = 0
CHAT_ID = 0

STATE = {
    "state": "starting",
    "note": "Starting Jarvis voice system...",
    "mode": "HYBRID",
    "mic": {"n": 0, "a": []},
    "last_you": "",
    "tool_active": False,
    "model": "Groq / Local",
    "t_rec": 0.0,
    "t_think": 0.0,
    "last_tool": "Waiting",
    "tools": 0,
    "facts": 0,
    "mail_age": None,
    "chat": [],
    "cards": [],
    "stocks": [],
    "sys": {}
}


def update_state(**values):
    with LOCK:
        STATE.update(values)


def add_chat(kind, message):
    global CHAT_ID

    with LOCK:
        CHAT_ID += 1

        STATE["chat"].append({
            "i": CHAT_ID,
            "k": kind,
            "x": str(message),
            "t": datetime.now().strftime("%H:%M:%S")
        })

        STATE["chat"] = STATE["chat"][-80:]


def add_mic_level(audio):
    global MIC_TOTAL

    try:
        raw = audio.get_raw_data(convert_rate=16000, convert_width=2)

        samples = array("h")
        samples.frombytes(raw)

        if not samples:
            return

        rms = math.sqrt(
            sum(sample * sample for sample in samples) / len(samples)
        )

        level = min(1.0, rms / 5000.0)

        with LOCK:
            MIC_TOTAL += 1
            MIC_HISTORY.append((MIC_TOTAL, round(level, 3)))

    except Exception as e:
        print("Microphone level error:", e)


def voice_worker():

    recognizer = sr.Recognizer()

    recognizer.energy_threshold = 35
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.0
    recognizer.non_speaking_duration = 0.5

    update_state(
        state="starting",
        note="Checking microphone..."
    )

    print("\nChecking microphone...")

    try:
        mic = sr.Microphone(device_index=1)

        with mic as source:

            print("Microphone connected.")
            print("Calibrating microphone...")

            recognizer.adjust_for_ambient_noise(
                source,
                duration=2
            )

            print("Microphone calibrated.")
            print("JARVIS VOICE SYSTEM READY.")

            update_state(
                state="listening",
                note="Microphone connected. Speak now."
            )

            add_chat("sys", "Jarvis voice system connected.")

            while not STOP_EVENT.is_set():

                try:
                    update_state(
                        state="listening",
                        note="Listening for your command...",
                        tool_active=False
                    )

                    audio = recognizer.listen(
                        source,
                        timeout=None,
                        phrase_time_limit=10
                    )

                    add_mic_level(audio)

                    update_state(
                        state="recognizing",
                        note="Recognizing your voice..."
                    )

                    start_rec = time.time()

                    query = recognizer.recognize_google(
                        audio,
                        language="en-IN"
                    ).strip()

                    rec_time = time.time() - start_rec

                    print("\nYou said:", query)

                    q_clean = query.lower().strip()

                    update_state(
                        t_rec=rec_time,
                        last_you=query
                    )

                    add_chat("you", query)

                    if q_clean in ["exit", "quit", "stop jarvis"]:
                        update_state(
                            state="speaking",
                            note="Shutting down voice system..."
                        )

                        jarvis_voice.speak("Goodbye!")

                        add_chat("sys", "Jarvis voice system stopped.")

                        STOP_EVENT.set()
                        break

                    if q_clean.startswith("jarvis"):
                        q_clean = q_clean[len("jarvis"):].strip(
                            " ,.!?"
                        )

                    if not q_clean:
                        update_state(
                            state="speaking",
                            note="Waiting for your command..."
                        )

                        jarvis_voice.speak("Yes, I'm listening.")
                        continue

                    update_state(
                        state="thinking",
                        note="Processing your command...",
                        last_tool=q_clean
                    )

                    start_think = time.time()

                    response = jarvis_brain.think(q_clean)

                    think_time = time.time() - start_think

                    if response is None:
                        response = "I could not complete that command."

                    print("\n[JARVIS]:", response)

                    add_chat("jarvis", response)

                    update_state(
                        state="speaking",
                        note="Preparing voice response...",
                        t_think=think_time
                    )

                    jarvis_voice.speak(response)

                except sr.UnknownValueError:
                    update_state(
                        state="listening",
                        note="I didn't catch that. Please repeat."
                    )

                except sr.RequestError as e:
                    print("Speech recognition error:", e)

                    update_state(
                        state="listening",
                        note="Speech recognition network error."
                    )

                    time.sleep(2)

                except KeyboardInterrupt:
                    STOP_EVENT.set()
                    break

                except Exception as e:
                    print("Voice worker error:", repr(e))

                    update_state(
                        state="listening",
                        note="Voice system encountered an error."
                    )

                    time.sleep(1)

    except Exception as e:
        print("\nMICROPHONE INITIALIZATION ERROR:", repr(e))

        update_state(
            state="off",
            note="Microphone could not start. Check device index and permissions."
        )

        add_chat("sys", "Microphone initialization failed.")

    finally:
        if STOP_EVENT.is_set():
            update_state(
                state="off",
                note="Jarvis voice system stopped."
            )


class JarvisHandler(BaseHTTPRequestHandler):

    def send_json(self, data):
        body = json.dumps(data).encode("utf-8")

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):

        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/state":

            params = parse_qs(parsed.query)

            try:
                last_seen = int(params.get("lv", [0])[0])
            except (ValueError, TypeError):
                last_seen = 0

            with LOCK:
                data = dict(STATE)

                data["chat"] = list(STATE["chat"])
                data["cards"] = list(STATE["cards"])
                data["stocks"] = list(STATE["stocks"])

                data["mic"] = {
                    "n": MIC_TOTAL,
                    "a": [
                        level
                        for seq, level in MIC_HISTORY
                        if seq > last_seen
                    ]
                }

            self.send_json(data)
            return

        if path == "/":

            if not HTML_FILE.exists():
                self.send_error(
                    404,
                    "jarvis_workplace.html not found"
                )
                return

            body = HTML_FILE.read_bytes()

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()

            self.wfile.write(body)
            return

        self.send_error(404, "Not found")

    def log_message(self, format, *args):
        print("[JARVIS WEB]", format % args)


def main():

    if not HTML_FILE.exists():
        print("ERROR: jarvis_workplace.html was not found.")
        return

    server = ThreadingHTTPServer(
        (HOST, PORT),
        JarvisHandler
    )

    voice_thread = threading.Thread(
        target=voice_worker,
        daemon=True
    )

    print("=" * 50)
    print("       JARVIS AI WORKPLACE")
    print("=" * 50)
    print(f"Interface: http://{HOST}:{PORT}")
    print("Starting microphone and voice system...")
    print("Press CTRL+C to stop Jarvis.")
    print("=" * 50)

    voice_thread.start()

    webbrowser.open(f"http://{HOST}:{PORT}")

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nStopping Jarvis...")

    finally:
        STOP_EVENT.set()
        server.server_close()
        print("Jarvis interface stopped.")


if __name__ == "__main__":
    main()
