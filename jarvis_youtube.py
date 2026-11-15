"""YouTube playback and controls for Jarvis on Windows."""

import time
import webbrowser

import pyautogui
import pygetwindow as gw
import yt_dlp

# Search results from the most recent Jarvis YouTube play command.
_video_queue = []
_current_index = -1
_browser_window = None


_BROWSER_MARKERS = (
    "microsoft edge",
    "google chrome",
    "mozilla firefox",
    "firefox",
    "brave",
    "opera",
)


def _is_browser_window(window):
    title = (getattr(window, "title", "") or "").lower()

    # Edge can include a zero-width character in its window title,
    # for example: "Microsoft\u200b Edge". Remove invisible characters
    # before checking the browser name.
    for invisible in ("\u200b", "\u200c", "\u200d", "\ufeff"):
        title = title.replace(invisible, "")

    title = " ".join(title.split())
    return bool(title.strip()) and any(
        marker in title for marker in _BROWSER_MARKERS
    )


def _remember_browser_window():
    """Remember the browser window opened/focused by the latest YouTube action."""
    global _browser_window

    try:
        active = gw.getActiveWindow()
        if active and _is_browser_window(active):
            _browser_window = active
            return True

        candidates = [w for w in gw.getAllWindows() if _is_browser_window(w)]

        # Prefer a browser window whose current tab title identifies YouTube.
        youtube_candidates = [
            w for w in candidates
            if "youtube" in (w.title or "").lower()
        ]
        if youtube_candidates:
            _browser_window = youtube_candidates[-1]
            return True

        if candidates:
            _browser_window = candidates[-1]
            return True

    except Exception as exc:
        print("[YouTube Window Detection]:", exc)

    return False


def _focus_youtube():
    """Focus the remembered browser window, not a VS Code file named youtube."""
    global _browser_window

    try:
        if _browser_window is None or not _is_browser_window(_browser_window):
            _remember_browser_window()

        if _browser_window is None:
            return False, (
                "I couldn't find a browser window. Open a YouTube video first."
            )

        if getattr(_browser_window, "isMinimized", False):
            _browser_window.restore()

        _browser_window.activate()
        time.sleep(0.7)
        return True, "YouTube browser focused."

    except Exception as exc:
        _browser_window = None
        return False, f"Could not focus the YouTube browser: {exc}"


def _navigate_in_browser(url):
    """Navigate the remembered browser window to a video URL."""
    focused, message = _focus_youtube()
    if not focused:
        return False, message

    try:
        pyautogui.hotkey("ctrl", "l")
        pyautogui.write(url, interval=0.002)
        pyautogui.press("enter")
        time.sleep(3)
        _remember_browser_window()
        return True, "YouTube video opened."
    except Exception as exc:
        return False, f"Could not open the YouTube video: {exc}"


def play(query):
    """Search YouTube, open the first result, and remember up to 10 results."""
    global _video_queue, _current_index, _browser_window

    try:
        options = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            results = ydl.extract_info(f"ytsearch10:{query}", download=False)

        entries = results.get("entries") or []
        _video_queue = [
            {"id": item.get("id"), "title": item.get("title") or query}
            for item in entries
            if item and item.get("id")
        ]

        if not _video_queue:
            _current_index = -1
            return False, f"No YouTube videos found for {query}."

        _current_index = 0
        first = _video_queue[0]
        url = f"https://www.youtube.com/watch?v={first['id']}&autoplay=1"

        # Open in a new tab; then remember the actual browser window.
        webbrowser.open(url, new=2)
        time.sleep(3)
        _remember_browser_window()

        return True, f"Opening {first['title']} on YouTube."

    except Exception as exc:
        return False, f"YouTube error: {exc}"


def pause():
    # Send YouTube the K shortcut to pause playback.
    focused, message = _focus_youtube()
    if not focused:
        return False, message

    try:
        pyautogui.press("k")
        return True, "YouTube pause command sent."
    except Exception as exc:
        return False, f"YouTube pause failed: {exc}"


def resume():
    # Send YouTube the K shortcut to resume playback.
    focused, message = _focus_youtube()
    if not focused:
        return False, message

    try:
        pyautogui.press("k")
        return True, "YouTube resume command sent."
    except Exception as exc:
        return False, f"YouTube resume failed: {exc}"


def stop():
    """Stop audible playback by pausing the current YouTube video."""
    success, message = pause()
    if success:
        return True, "YouTube playback stopped (video paused)."
    return False, message


def next_video():
    """Open the next result from the most recent search."""
    global _current_index

    if _video_queue and 0 <= _current_index < len(_video_queue) - 1:
        next_index = _current_index + 1
        item = _video_queue[next_index]
        url = f"https://www.youtube.com/watch?v={item['id']}&autoplay=1"
        success, message = _navigate_in_browser(url)
        if success:
            _current_index = next_index
            return True, f"Playing next result: {item['title']}."
        return False, message

    focused, message = _focus_youtube()
    if not focused:
        return False, message

    try:
        pyautogui.hotkey("shift", "n")
        return True, "YouTube next-video shortcut sent."
    except Exception as exc:
        return False, f"YouTube next failed: {exc}"


def previous_video():
    """Open the previous result from the most recent search."""
    global _current_index

    if _video_queue and 0 < _current_index < len(_video_queue):
        previous_index = _current_index - 1
        item = _video_queue[previous_index]
        url = f"https://www.youtube.com/watch?v={item['id']}&autoplay=1"
        success, message = _navigate_in_browser(url)
        if success:
            _current_index = previous_index
            return True, f"Playing previous result: {item['title']}."
        return False, message

    focused, message = _focus_youtube()
    if not focused:
        return False, message

    try:
        pyautogui.hotkey("shift", "p")
        return True, "YouTube previous-video shortcut sent."
    except Exception as exc:
        return False, f"YouTube previous failed: {exc}"
