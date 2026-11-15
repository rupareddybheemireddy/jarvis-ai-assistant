
"""
jarvis_actions.py - Windows Jarvis automation
Spotify desktop, YouTube, WhatsApp, apps, websites,
volume, date/time and existing utilities.
"""

import subprocess
import re
import urllib.parse
import datetime
import os
import glob
import shutil
import webbrowser
import ctypes
import time
import tkinter as tk
import pyautogui
import pygetwindow as gw

import jarvis_market
import jarvis_spotify
import jarvis_youtube


SITES = {
    "youtube": "https://www.youtube.com",
    "whatsapp": "https://web.whatsapp.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "maps": "https://maps.google.com",
    "calendar": "https://calendar.google.com",
    "drive": "https://drive.google.com",
}

ALIASES = {
    "vs code": "code",
    "visual studio code": "code",
    "chrome": "chrome",
    "google chrome": "chrome",
    "word": "winword",
    "microsoft word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "settings": "ms-settings:",
    "system settings": "ms-settings:",
    "terminal": "wt",
}

FAVOURITE_ALBUM_URL = (
    "https://open.spotify.com/album/3ukkRHDHbN8tNRPKsGZR1h"
)

_PENDING_WHATSAPP = None


# ============================================================
# GENERAL APPLICATION LAUNCHING
# ============================================================

def _open(args):
    """Open a website or Windows application."""
    try:
        if not args:
            return False

        target = args[0]

        if target.startswith(("http://", "https://")):
            return bool(webbrowser.open(target))

        os.startfile(target)
        return True

    except Exception as e:
        print("[Windows Open Error]:", e)
        return False


def _apps():
    """Find applications in Windows Start Menu."""
    apps = {}

    folders = [
        os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs"
        ),
        os.path.join(
            os.environ.get("PROGRAMDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs"
        ),
    ]

    for folder in folders:
        if not os.path.isdir(folder):
            continue

        for path in glob.glob(
            os.path.join(folder, "**", "*.lnk"),
            recursive=True
        ):
            name = os.path.splitext(os.path.basename(path))[0]
            apps[name.lower()] = path

    return apps


def find_app(name):
    """Find an installed Windows application."""
    name = name.lower().strip()
    name = ALIASES.get(name, name)

    executable = shutil.which(name)

    if executable:
        return executable

    apps = _apps()

    if name in apps:
        return apps[name]

    for app_name, path in apps.items():
        if name in app_name:
            return path

    return None


# ============================================================
# SPOTIFY DESKTOP APPLICATION
# ============================================================

def find_spotify_desktop():
    """Find the installed Spotify desktop application."""

    # First check whether Spotify is already running.
    try:
        window = jarvis_spotify.find_spotify_window()

        if window:
            return "RUNNING"

    except Exception:
        pass

    # Search Windows Start Menu shortcuts.
    apps = _apps()

    for app_name, path in apps.items():
        if app_name == "spotify" or app_name.startswith("spotify "):
            return path

    # Check common Windows installation locations.
    local = os.environ.get("LOCALAPPDATA", "")
    roaming = os.environ.get("APPDATA", "")
    program_files = os.environ.get("PROGRAMFILES", "")

    possible_paths = [
        os.path.join(roaming, "Spotify", "Spotify.exe"),
        os.path.join(local, "Programs", "Spotify", "Spotify.exe"),
        os.path.join(local, "Spotify", "Spotify.exe"),
        os.path.join(program_files, "Spotify", "Spotify.exe"),
    ]

    for path in possible_paths:
        if path and os.path.isfile(path):
            return path

    # Check PATH for Spotify executable.
    executable = shutil.which("Spotify.exe")

    if executable:
        return executable

    return None


def launch_spotify_desktop():
    """Launch the actual installed Spotify Windows application."""

    try:
        target = find_spotify_desktop()

        if target == "RUNNING":
            return True, "Spotify desktop application is already running."

        if target is None:
            return False, (
                "I couldn't find the Spotify desktop application. "
                "Please install Spotify for Windows."
            )

        if target.lower().endswith(".lnk"):
            os.startfile(target)

        elif target.lower().endswith(".exe"):
            subprocess.Popen([target])

        else:
            return False, "Spotify desktop application path is invalid."

        print("[Spotify] Desktop application launched.")

        # Give Spotify time to create its window.
        for _ in range(15):
            time.sleep(1)

            try:
                window = jarvis_spotify.find_spotify_window()

                if window:
                    return True, "Spotify desktop application opened."

            except Exception:
                pass

        return True, (
            "Spotify desktop launch command submitted. "
            "Please check whether its window appeared."
        )

    except Exception as e:
        print("[Spotify Desktop Error]:", repr(e))
        return False, f"Could not launch Spotify desktop: {e}"


def launch_app(name):
    """Launch a Windows application."""

    name = name.lower().strip()
    target = ALIASES.get(name, name)

    try:
        # Spotify must always use its desktop application.
        if name == "spotify":
            success, message = launch_spotify_desktop()
            return success

        if target.endswith(":"):
            os.startfile(target)
            return True

        app = find_app(name)

        if app:
            os.startfile(app)
            return True

        if shutil.which(target):
            subprocess.Popen([target])
            return True

        return False

    except Exception as e:
        print("[App Launch Error]:", e)
        return False


# ============================================================
# WINDOWS MEDIA AND VOLUME CONTROLS
# ============================================================

def media_control(action):
    """Send Windows multimedia keys."""

    keys = {
        "play_pause": 0xB3,
        "next": 0xB0,
        "previous": 0xB1,
    }

    if action not in keys:
        return False

    try:
        key = keys[action]
        ctypes.windll.user32.keybd_event(key, 0, 0, 0)
        ctypes.windll.user32.keybd_event(key, 0, 2, 0)
        return True

    except Exception as e:
        print("[Media Control Error]:", e)
        return False


def change_volume(action):
    """Control Windows system volume."""

    keys = {
        "up": 0xAF,
        "down": 0xAE,
        "mute": 0xAD,
    }

    try:
        key = keys[action]
        ctypes.windll.user32.keybd_event(key, 0, 0, 0)
        ctypes.windll.user32.keybd_event(key, 0, 2, 0)
        return True

    except Exception as e:
        print("[Volume Error]:", e)
        return False


def spotify_search(query):
    """Legacy Spotify browser search. Not used for desktop commands."""

    url = (
        "https://open.spotify.com/search/"
        + urllib.parse.quote(query)
    )

    return _open([url])


def youtube_search(query):
    """Open YouTube search results."""

    url = (
        "https://www.youtube.com/results?search_query="
        + urllib.parse.quote(query)
    )

    return _open([url])


# ============================================================
# WHATSAPP FUNCTIONS
# ============================================================

def find_whatsapp_window():
    """Find WhatsApp or its Microsoft Edge browser window."""

    windows = [
        window
        for window in gw.getAllWindows()
        if window.title and window.title.strip()
    ]

    whatsapp_windows = [
        window for window in windows
        if "whatsapp" in window.title.lower()
    ]

    if whatsapp_windows:
        return whatsapp_windows[0]

    edge_windows = [
        window for window in windows
        if "edge" in window.title.replace("\u200b", "").lower()
    ]

    if edge_windows:
        return max(
            edge_windows,
            key=lambda window: max(1, window.width) * max(1, window.height)
        )

    return None


def activate_whatsapp_window():
    """Activate and maximize WhatsApp browser window."""

    try:
        window = find_whatsapp_window()

        if window is None:
            return False, "I couldn't find the browser window."

        if window.isMinimized:
            window.restore()
            time.sleep(1)

        window.activate()
        time.sleep(1)

        window.maximize()
        time.sleep(1)

        pyautogui.click(
            window.left + int(window.width * 0.60),
            window.top + int(window.height * 0.45)
        )

        time.sleep(0.5)

        return True, "WhatsApp browser activated."

    except Exception as e:
        return False, f"Browser activation failed: {e}"


def focus_whatsapp_composer():
    """Focus the WhatsApp message box."""

    try:
        success, result = activate_whatsapp_window()

        if not success:
            return False, result

        window = find_whatsapp_window()

        if window is None:
            return False, "WhatsApp browser window not found."

        x = window.left + int(window.width * 0.55)
        y = window.top + window.height - 85

        pyautogui.click(x, y)
        time.sleep(0.5)

        return True, "WhatsApp message box focused."

    except Exception as e:
        return False, f"Could not focus WhatsApp: {e}"


def copy_to_clipboard(message):
    """Copy exact text to Windows clipboard."""

    root = tk.Tk()
    root.withdraw()

    try:
        root.clipboard_clear()
        root.clipboard_append(message)
        root.update()

    finally:
        root.destroy()


def send_whatsapp_message(
    contact_name,
    message="Hello from Jarvis"
):
    """Search for a WhatsApp contact without sending a message."""

    global _PENDING_WHATSAPP

    if _PENDING_WHATSAPP is not None:
        return (
            "Another WhatsApp message is already pending. "
            "Please finish or cancel it first."
        )

    opened = _open([SITES["whatsapp"]])

    if not opened:
        return "I couldn't open WhatsApp Web."

    try:
        time.sleep(8)

        success, result = activate_whatsapp_window()

        if not success:
            return result

        pyautogui.hotkey("ctrl", "alt", "n")
        time.sleep(2)

        copy_to_clipboard(contact_name)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(3)

        pyautogui.press("enter")
        time.sleep(3)

        _PENDING_WHATSAPP = {
            "contact": contact_name,
            "message": message,
            "stage": "awaiting_contact"
        }

        return (
            f"I searched WhatsApp for {contact_name} "
            "and attempted to open the first matching chat. "
            "Please check the chat header and verify the contact. "
            "If it is correct, say chat ready. "
            "I will prepare your message without sending it."
        )

    except Exception as e:
        _PENDING_WHATSAPP = None
        return f"WhatsApp contact search failed: {e}"


def handle_whatsapp_followup(command):
    """Handle contact verification, message preparation and confirmation."""

    global _PENDING_WHATSAPP

    if _PENDING_WHATSAPP is None:
        return None

    command = command.lower().strip(" .,!?")

    cancel_commands = {
        "no",
        "no cancel",
        "cancel",
        "cancel message",
        "cancel whatsapp",
        "no don't send",
        "do not send",
        "don't send",
        "discard message"
    }

    if command in cancel_commands:
        contact = _PENDING_WHATSAPP["contact"]
        _PENDING_WHATSAPP = None

        return (
            f"Cancelled the WhatsApp message for {contact}. "
            "No message was sent."
        )

    stage = _PENDING_WHATSAPP["stage"]

    if command in (
        "chat ready",
        "contact ready",
        "chat is ready"
    ):

        if stage != "awaiting_contact":
            return (
                "Your message is already prepared. "
                "Please review it and say send message "
                "or cancel message."
            )

        success, result = focus_whatsapp_composer()

        if not success:
            return result

        try:
            message = _PENDING_WHATSAPP["message"]

            copy_to_clipboard(message)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.7)

            _PENDING_WHATSAPP["stage"] = "awaiting_confirmation"

            contact = _PENDING_WHATSAPP["contact"]

            return (
                f"Message prepared for {contact}. "
                f"The message is: {message}. "
                "Please verify the recipient and message. "
                "Say yes, send it to confirm, "
                "or no, cancel to cancel."
            )

        except Exception as e:
            return f"Could not prepare the message: {e}"

    send_commands = {
        "yes",
        "yes send",
        "yes send it",
        "send it",
        "send message",
        "confirm send",
        "yes confirm"
    }

    if command in send_commands:

        if stage != "awaiting_confirmation":
            return (
                "The message is not ready yet. "
                "First verify the contact and say chat ready."
            )

        success, result = focus_whatsapp_composer()

        if not success:
            return result

        try:
            pyautogui.press("enter")
            time.sleep(0.5)

            contact = _PENDING_WHATSAPP["contact"]
            _PENDING_WHATSAPP = None

            return (
                f"Send command submitted for {contact}. "
                "Please check WhatsApp to verify delivery."
            )

        except Exception as e:
            return f"Sending failed: {e}"

    if stage == "awaiting_contact":
        return (
            "Please verify the WhatsApp contact in the chat header. "
            "Then say chat ready, or say cancel."
        )

    if stage == "awaiting_confirmation":
        return (
            "Your message is waiting for confirmation. "
            "Say yes, send it to send, or no, cancel to cancel."
        )

    return None


# ============================================================
# EMAIL BRIEFING
# ============================================================

def get_mail_brief():
    """Read locally saved mail cache."""

    cache_file = os.path.expanduser(
        "~/.openjarvis/mail_cache.txt"
    )

    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", errors="ignore") as f:
                content = f.read().strip()

                if content:
                    return (
                        "Here is your saved mail briefing: "
                        + content[:600]
                    )

        except Exception as e:
            print("[Mail Error]:", e)

    return (
        "I couldn't find a saved mail briefing. "
        "Gmail is not connected to Jarvis yet."
    )


# ============================================================
# MAIN ACTION HANDLER
# ============================================================

def try_action(q):
    """Execute local actions. Return None if not handled."""

    if not isinstance(q, str):
        return None

    original_q = q.strip()
    q_clean = original_q.lower().strip(" .,!?")

    # ========================================================
    # WHATSAPP
    # ========================================================

    whatsapp_response = handle_whatsapp_followup(q_clean)

    if whatsapp_response is not None:
        return whatsapp_response

    m = re.search(
        r"(?:send|reply|message)\s+"
        r"(?:on\s+whatsapp\s+to|whatsapp\s+to|to)\s+"
        r"(.+?)(?:\s+saying\s+(.+))?$",
        original_q,
        re.IGNORECASE
    )

    if "whatsapp" in q_clean and m:
        contact = m.group(1).strip()

        msg = (
            m.group(2).strip()
            if m.group(2)
            else "I received your message, will get back shortly."
        )

        return send_whatsapp_message(contact, msg)

    if q_clean in ("open whatsapp", "check whatsapp", "whatsapp"):
        _open([SITES["whatsapp"]])
        return "Opening WhatsApp."

    # ========================================================
    # YOUTUBE — EXISTING WORKING CODE PRESERVED
    # ========================================================

    if "youtube" in q_clean or "you tube" in q_clean:

        if re.search(r"\b(stop|halt)\b", q_clean):
            success, message = jarvis_youtube.stop()
            return message

        if re.search(r"\b(pause|pass)\b", q_clean):
            success, message = jarvis_youtube.pause()
            return message

        if re.search(r"\b(next|skip)\b", q_clean):
            success, message = jarvis_youtube.next_video()
            return message

        if re.search(r"\b(previous|back)\b", q_clean):
            success, message = jarvis_youtube.previous_video()
            return message

        if re.search(r"\b(resume|continue|unpause)\b", q_clean):
            success, message = jarvis_youtube.resume()
            return message

        match = re.search(
            r"(?:\band\s*play|\bandplay|\bplay)\s+(.+?)\s*$",
            original_q,
            re.IGNORECASE
        )

        if match:
            query = match.group(1).strip()

            query = re.sub(
                r"\s+(?:on|in)\s+(?:you\s*tube|youtube)$",
                "",
                query,
                flags=re.IGNORECASE
            ).strip(" .,!? ")

            if query:
                success, message = jarvis_youtube.play(query)
                return message

        search_match = re.search(
            r"(?:search|find)\s+(.+?)(?:\s+(?:on|in)\s+(?:you\s*tube|youtube))?$",
            original_q,
            re.IGNORECASE
        )

        if search_match:
            query = search_match.group(1).strip(" .,!? ")
            youtube_search(query)
            return f"Searching YouTube for {query}."

        _open([SITES["youtube"]])
        return "Opening YouTube."

    # ========================================================
    # SPOTIFY — DESKTOP APPLICATION ONLY
    # ========================================================

    spotify_command = re.sub(
        r"^\s*jarvis[\s,:-]*",
        "",
        original_q,
        flags=re.IGNORECASE
    )

    spotify_command = re.sub(
        r"\s+(?:on|in)\s+spotify[.!?]*$",
        "",
        spotify_command,
        flags=re.IGNORECASE
    ).strip()

    # Detect explicit Spotify commands and the favourite album.
    spotify_requested = (
        "spotify" in q_clean
        or "arirang" in q_clean
        or "favourite album" in q_clean
        or "favorite album" in q_clean
    )

    if spotify_requested:

        # Opening Spotify means opening the installed desktop app.
        if q_clean in (
            "spotify",
            "open spotify",
            "launch spotify",
            "start spotify"
        ):
            success, message = launch_spotify_desktop()
            return message

        # Start the desktop application before running automation.
        # This allows jarvis_spotify.py to find the existing window
        # instead of activating the spotify: browser protocol.
        success, launch_message = launch_spotify_desktop()

        if not success:
            return launch_message

        try:
            spotify_result = jarvis_spotify.handle(spotify_command)

            if isinstance(spotify_result, tuple):
                handled = bool(spotify_result[0])

                response = (
                    str(spotify_result[1])
                    if len(spotify_result) > 1
                    else "Spotify command processed."
                )

                if handled:
                    return response

                return response

            if spotify_result is not None:
                return spotify_result

        except Exception as e:
            print("[Spotify Automation Error]:", repr(e))
            return (
                "Spotify desktop opened, but I encountered "
                "an error while controlling playback."
            )

        return (
            "Spotify desktop opened, but I couldn't "
            "understand the Spotify command."
        )

    # ========================================================
    # STOCK MARKET
    # ========================================================

    if any(k in q_clean for k in (
        "stock", "market", "nifty", "sensex",
        "crypto", "bitcoin", "buy or sell"
    )):
        for sym, name in jarvis_market.DEFAULT_TICKERS.items():

            if (
                name.lower() in q_clean
                or sym.lower().replace(".ns", "") in q_clean
            ):
                data = jarvis_market.analyze_ticker(sym)

                if data:
                    direction = (
                        "up" if data["pct_change"] >= 0 else "down"
                    )

                    return (
                        f"{data['name']} is trading at "
                        f"{data['currency']}{data['price']:,}, "
                        f"{direction} {abs(data['pct_change'])}%. "
                        f"Technical indicator: {data['signal']}. "
                        f"{data['reason']}"
                    )

        return (
            "Here is the market overview: "
            + jarvis_market.market_briefing()
        )

    # ========================================================
    # EMAIL
    # ========================================================

    if any(k in q_clean for k in (
        "mail brief", "check mail", "read emails",
        "inbox summary", "unread emails"
    )):
        return get_mail_brief()

    # ========================================================
    # GOOGLE SEARCH
    # ========================================================

    match = re.match(
        r"(?:search|google)(?: for)?\s+(.+)",
        q_clean
    )

    if match:
        query = match.group(1).strip()

        url = (
            "https://www.google.com/search?q="
            + urllib.parse.quote(query)
        )

        _open([url])
        return f"Searching Google for {query}."

    # ========================================================
    # OPEN WEBSITES AND APPLICATIONS
    # ========================================================

    match = re.match(
        r"(?:please\s+)?(?:open|launch|start)\s+(.+)",
        q_clean
    )

    if match:
        name = match.group(1).strip()

        if name in SITES:
            _open([SITES[name]])
            return f"Opening {name}."

        if launch_app(name):
            return f"Opening {name}."

        return (
            f"I couldn't find {name}. "
            "Please check whether it is installed."
        )

    # ========================================================
    # WINDOWS VOLUME
    # ========================================================

    if "volume up" in q_clean or "louder" in q_clean:
        if change_volume("up"):
            return "Volume increased."

    if "volume down" in q_clean or "quieter" in q_clean:
        if change_volume("down"):
            return "Volume decreased."

    if q_clean in ("mute", "mute volume", "mute the volume"):
        if change_volume("mute"):
            return "System audio mute toggled."

    # ========================================================
    # DATE AND TIME
    # ========================================================

    if "time" in q_clean:
        return (
            "It is currently "
            + datetime.datetime.now().strftime("%I:%M %p")
        )

    if "date" in q_clean or "today" in q_clean:
        return (
            "Today is "
            + datetime.datetime.now().strftime("%A, %B %d, %Y")
        )

    return None
