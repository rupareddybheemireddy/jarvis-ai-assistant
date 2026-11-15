
"""
Jarvis Brain - Groq AI + local Windows actions
"""

import os
import time
import re

from openai import OpenAI

import jarvis_actions
import jarvis_spotify


KEYFILE = os.path.expanduser("~/.openjarvis/free.key")

MODELS = [
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "qwen/qwen3-32b",
]

_client = None
_client_key = None
_history = []
_cooldown_until = 0.0


SYSTEM_PROMPT = """
You are Jarvis, a helpful Windows desktop voice assistant.

Understand natural language commands and respond naturally.
Keep answers short because you are speaking aloud.

You can explain how to use apps, answer questions,
and help the user with everyday laptop tasks.

Never claim that you performed an action unless it was
actually completed by the local action system.
"""


def _get_api_key():
    key = os.environ.get("GROQ_API_KEY", "").strip()

    if key:
        return key

    if os.path.exists(KEYFILE):
        try:
            with open(KEYFILE, "r", encoding="utf-8") as file:
                return file.read().strip()

        except OSError as error:
            print("[Key File Error]:", error)

    return None


def ready():
    return bool(_get_api_key()) and time.time() >= _cooldown_until


def _is_spotify_control_command(question):
    """Identify playback controls that must go directly to Spotify."""
    text = question.lower().strip()
    text = text.replace("jarvis", "").strip(" ,.!?")

    phrases = (
        "pause",
        "pause the song",
        "pause the music",
        "stop",
        "stop the song",
        "stop the music",
        "stop playing",
        "resume",
        "resume the song",
        "resume the music",
        "resume music",
        "continue",
        "continue playing",
        "play again",
        "unpause",
        "next",
        "next song",
        "next track",
        "skip",
        "skip song",
        "previous",
        "previous song",
        "previous track",
        "last song",
        "go back",
    )

    return text in phrases


def _retry_after_seconds(error, default=60):
    message = str(error).lower()

    patterns = [
        r"try again in\s*(\d+)m\s*([0-9]+(?:\.[0-9]+)?)s",
        r"try again in\s*([0-9]+(?:\.[0-9]+)?)s",
    ]

    match = re.search(patterns[0], message)

    if match:
        return int(
            float(match.group(1)) * 60 +
            float(match.group(2))
        ) + 2

    match = re.search(patterns[1], message)

    if match:
        return int(float(match.group(1))) + 2

    return default


def _is_rate_limited(error):
    status = getattr(error, "status_code", None)
    message = str(error).lower()

    return status == 429 or any(word in message for word in (
        "429",
        "rate limit",
        "too many requests",
        "rate_limit",
        "exceeded",
    ))


def _set_cooldown(seconds):
    global _cooldown_until

    _cooldown_until = max(
        _cooldown_until,
        time.time() + float(seconds)
    )


def _local_fallback(question):
    try:
        result = jarvis_actions.try_action(question)

        if result:
            return result

    except Exception as error:
        print("[Local Action Error]:", error)

    return (
        "My cloud AI is temporarily unavailable. "
        "I can still handle the local commands that are configured."
    )


def think(question):
    global _client, _client_key, _history

    question = question.strip()

    if not question:
        return "Please tell me what you want me to do."

    # Handle Spotify playback controls directly.
    # These commands should not be sent to Groq.
    if _is_spotify_control_command(question):
        try:
            success, message = jarvis_spotify.handle(question)

            if success:
                return message

            print("[Spotify Control Error]:", message)

        except Exception as error:
            print("[Spotify Control Error]:", error)

    # Run other configured local actions.
    try:
        local_result = jarvis_actions.try_action(question)

        if local_result:
            return local_result

    except Exception as error:
        print("[Local Action Error]:", error)

    key = _get_api_key()

    if not key:
        print("[Groq Error]: API key not found.")
        return _local_fallback(question)

    if time.time() < _cooldown_until:
        return _local_fallback(question)

    if _client is None or key != _client_key:
        _client = OpenAI(
            api_key=key,
            base_url="https://api.groq.com/openai/v1",
            timeout=30.0,
            max_retries=1,
        )

        _client_key = key

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + _history[-6:]
        + [{"role": "user", "content": question}]
    )

    for model in MODELS:
        try:
            print(f"[Jarvis AI]: Trying {model}...")

            response = _client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=350,
                temperature=0.6,
            )

            answer = response.choices[0].message.content or ""
            answer = answer.strip()

            if answer:
                _history.extend([
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": answer},
                ])

                _history = _history[-12:]

                return answer

        except Exception as error:
            if _is_rate_limited(error):
                wait_seconds = _retry_after_seconds(error)
                _set_cooldown(wait_seconds)

                print(
                    f"[Rate Limit]: Waiting {wait_seconds} seconds."
                )

                return _local_fallback(question)

            print(f"[Model {model} failed]: {error}")

    return _local_fallback(question)


if __name__ == "__main__":
    print("Testing Jarvis Brain...")
    print("API key found:", bool(_get_api_key()))
    print("Time test:", think("what time is it"))
    print("AI test:", think("explain what you can help me with"))
