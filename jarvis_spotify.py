
"""
jarvis_spotify.py
Windows Spotify desktop automation.
"""

import argparse
import os
import subprocess
import time

import pyautogui
import pygetwindow as gw

try:
    from pywinauto import Desktop
except ImportError:
    Desktop = None


APP_NAME = "Spotify"
WAIT_AFTER_OPEN = 5
WAIT_FOR_SEARCH = 3
WAIT_FOR_RESULTS = 5


def find_spotify_window():
    """Find the Spotify desktop window."""
    windows = gw.getWindowsWithTitle(APP_NAME)
    windows = [w for w in windows if w.title.strip()]
    return windows[0] if windows else None


def activate_spotify():
    """Open Spotify if necessary and activate its window."""
    window = find_spotify_window()

    if window is None:
        try:
            os.startfile("spotify:")
        except Exception:
            try:
                subprocess.Popen(
                    ["cmd", "/c", "start", "", "spotify:"],
                    shell=False
                )
            except Exception as exc:
                return False, f"Could not launch Spotify: {exc}"

        time.sleep(WAIT_AFTER_OPEN)
        window = find_spotify_window()

    if window is None:
        return False, "Spotify desktop window was not found."

    try:
        if window.isMinimized:
            window.restore()

        window.activate()
        time.sleep(1)

        return True, "Spotify is ready."

    except Exception as exc:
        return False, f"Could not activate Spotify: {exc}"


def spotify_search(query):
    """Search for a song, artist or album inside Spotify."""
    if not query or not query.strip():
        return False, "Please provide a song or album name."

    success, message = activate_spotify()

    if not success:
        return False, message

    try:
        pyautogui.hotkey("ctrl", "k")
        time.sleep(1)

        pyautogui.hotkey("ctrl", "a")
        pyautogui.write(query.strip(), interval=0.04)
        time.sleep(WAIT_FOR_SEARCH)

        pyautogui.press("enter")
        time.sleep(WAIT_FOR_RESULTS)

        return True, f"Spotify search opened for {query}."

    except Exception as exc:
        return False, f"Spotify search failed: {exc}"


def find_play_button():
    """Try to locate a Spotify Play button through UI Automation."""
    if Desktop is None:
        return False

    try:
        desktop = Desktop(backend="uia")

        for window in desktop.windows():
            if "spotify" not in window.window_text().lower():
                continue

            buttons = window.descendants(control_type="Button")

            for button in buttons:
                try:
                    name = button.window_text().strip().lower()

                    if name == "play":
                        if button.is_visible() and button.is_enabled():
                            button.click_input()
                            return True

                except Exception:
                    continue

    except Exception:
        pass

    return False


def play(query):
    """Search for a query and attempt to start playback."""
    success, message = spotify_search(query)

    if not success:
        return False, message

    try:
        pyautogui.press("tab")
        time.sleep(0.5)

        if find_play_button():
            time.sleep(2)
            return True, f"Started playback for {query}."

        pyautogui.press("enter")
        time.sleep(4)

        return True, (
            f"Sent playback command for {query}. "
            "Please check Spotify to confirm the song started."
        )

    except Exception as exc:
        return False, f"Could not start playback: {exc}"


def media_key(key):
    """Send a Windows multimedia key."""
    keys = {
        "play_pause": "playpause",
        "next": "nexttrack",
        "previous": "prevtrack",
    }

    if key not in keys:
        return False, "Unsupported media command."

    try:
        success, message = activate_spotify()

        if not success:
            return False, message

        pyautogui.press(keys[key])
        time.sleep(1)

        return True, f"Spotify {key.replace('_', ' ')} command sent."

    except Exception as exc:
        return False, f"Media control failed: {exc}"



def pause():
    try:
        pyautogui.press("playpause")
        time.sleep(1)
        return True, "Spotify pause command sent."
    except Exception as exc:
        return False, f"Pause failed: {exc}"


def resume():
    try:
        pyautogui.press("playpause")
        time.sleep(1)
        return True, "Spotify resume command sent."
    except Exception as exc:
        return False, f"Resume failed: {exc}"


def next_track():
    return media_key("next")


def previous_track():
    return media_key("previous")


def handle(command):
    """Handle Spotify commands from Jarvis."""
    text = command.lower().strip()
    text = text.replace("jarvis", "").strip(" ,.!?")

    # Favourite BTS album
    if any(phrase in text for phrase in (
        "arirang",
        "favourite album",
        "favorite album"
    )):
        return play("BTS ARIRANG album")

    # Pause / stop
    if any(phrase in text for phrase in (
        "pause",
        "stop",
        "stop the song",
        "stop the music",
        "stop playing",
        "pause the song",
        "pause the music"
    )):
        return pause()

    # Resume / continue
    if any(phrase in text for phrase in (
        "resume",
        "continue",
        "continue playing",
        "resume music",
        "resume the song",
        "play again",
        "unpause"
    )):
        return resume()

    # Next track
    if any(phrase in text for phrase in (
        "next",
        "skip",
        "next song",
        "next track"
    )):
        return next_track()

    # Previous track
    if any(phrase in text for phrase in (
        "previous",
        "previous song",
        "previous track",
        "last song",
        "go back"
    )):
        return previous_track()

    # Search and play
    for prefix in ("play ", "search ", "find ", "open "):
        if text.startswith(prefix):
            query = text[len(prefix):].strip()

            for suffix in (" on spotify", " in spotify"):
                if query.endswith(suffix):
                    query = query[:-len(suffix)].strip()

            if query:
                return play(query)

    # Open Spotify
    if text in ("spotify", "open spotify", "launch spotify"):
        return activate_spotify()

    return False, "I couldn't understand that Spotify command."


def main():
    parser = argparse.ArgumentParser(
        description="Control Spotify desktop application"
    )

    parser.add_argument("--play", help="Search and play a song or album")
    parser.add_argument("--pause", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--next", action="store_true")
    parser.add_argument("--previous", action="store_true")
    parser.add_argument("--inspect", action="store_true")

    args = parser.parse_args()

    if args.play:
        result = play(args.play)
    elif args.pause:
        result = pause()
    elif args.resume:
        result = resume()
    elif args.next:
        result = next_track()
    elif args.previous:
        result = previous_track()
    elif args.inspect:
        success, message = activate_spotify()
        print(message)

        if success and Desktop is not None:
            try:
                desktop = Desktop(backend="uia")

                for window in desktop.windows():
                    if "spotify" in window.window_text().lower():
                        print("Window:", window.window_text())

                        for button in window.descendants(
                            control_type="Button"
                        ):
                            try:
                                print("Button:", button.window_text())
                            except Exception:
                                pass

            except Exception as exc:
                print("Inspection error:", exc)

        return
    else:
        parser.print_help()
        return

    success, message = result
    print(message)


if __name__ == "__main__":
    main()
