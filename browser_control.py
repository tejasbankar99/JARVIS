"""
browser_control.py — JARVIS Browser & Web Automation
=====================================================
Controls Chrome/browser for:
  - YouTube search & play
  - Google search
  - Any website navigation
  - Tab management
Uses webbrowser for simple opens + pyautogui for in-browser control.
Selenium is used if available for full automation.
"""

import time
import webbrowser
import subprocess
import re
from urllib.parse import quote_plus


# ── Simple URL-based controls (no extra deps) ─────────────────────────────────

def youtube_search(query: str) -> str:
    """Open YouTube and search for a query."""
    url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    webbrowser.open(url)
    return f"🎬 Searching YouTube for **'{query}'**, sir."


def youtube_play(query: str) -> str:
    """Search YouTube and auto-play the first result."""
    # Use ytsearch URL pattern — opens first result directly
    url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    webbrowser.open(url)
    time.sleep(2.5)
    # Click first result via pyautogui
    try:
        import pyautogui, time
        time.sleep(1.5)
        # Find and click first video thumbnail (approximate screen coords for typical YouTube layout)
        # More reliable: use keyboard shortcut — Tab to first result and Enter
        pyautogui.hotkey("ctrl", "l")   # Focus address bar
        time.sleep(0.3)
        pyautogui.hotkey("alt", "d")
        time.sleep(0.2)
        pyautogui.press("tab")
        time.sleep(0.5)
        # Press Tab until reaching first video result (~3-4 tabs from top)
        for _ in range(4):
            pyautogui.press("tab")
            time.sleep(0.1)
        pyautogui.press("enter")
        return f"🎬 Playing **'{query}'** on YouTube, sir."
    except Exception:
        return f"🎬 Opened YouTube search for **'{query}'**. Click the first result to play, sir."


def google_search(query: str) -> str:
    """Open Google search results."""
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    webbrowser.open(url)
    return f"🔍 Opened Google search for **'{query}'**, sir."


def open_website(url: str) -> str:
    """Open any URL in the default browser."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    domain = url.split("/")[2]
    return f"🌐 Opening **{domain}** in your browser, sir."


def open_spotify_web(query: str = "") -> str:
    """Open Spotify web player, optionally searching."""
    if query:
        url = f"https://open.spotify.com/search/{quote_plus(query)}"
    else:
        url = "https://open.spotify.com"
    webbrowser.open(url)
    return f"🎵 Opening Spotify{f' — searching for **{query}**' if query else ''}, sir."


def open_netflix() -> str:
    """Open Netflix."""
    webbrowser.open("https://www.netflix.com")
    return "🎬 Opening Netflix, sir."


def open_gmail() -> str:
    """Open Gmail."""
    webbrowser.open("https://mail.google.com")
    return "📧 Opening Gmail, sir."


def open_google_maps(location: str = "") -> str:
    """Open Google Maps for a location."""
    if location:
        url = f"https://www.google.com/maps/search/{quote_plus(location)}"
    else:
        url = "https://www.google.com/maps"
    webbrowser.open(url)
    return f"🗺️ Opening Google Maps{f' for **{location}**' if location else ''}, sir."


def open_whatsapp_web() -> str:
    """Open WhatsApp Web."""
    webbrowser.open("https://web.whatsapp.com")
    return "💬 Opening WhatsApp Web, sir."


def open_chatgpt() -> str:
    """Open ChatGPT."""
    webbrowser.open("https://chat.openai.com")
    return "🤖 Opening ChatGPT in your browser, sir."


def close_browser_tab() -> str:
    """Close the current browser tab."""
    try:
        import pyautogui
        pyautogui.hotkey("ctrl", "w")
        return "Closed the current tab, sir."
    except Exception as e:
        return f"Couldn't close tab: {e}"


def new_browser_tab(url: str = "") -> str:
    """Open a new browser tab."""
    try:
        import pyautogui
        pyautogui.hotkey("ctrl", "t")
        if url:
            time.sleep(0.4)
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            pyautogui.typewrite(url, interval=0.03)
            pyautogui.press("enter")
        return f"Opened new tab{f' at {url}' if url else ''}, sir."
    except Exception as e:
        return f"Couldn't open new tab: {e}"


def scroll_page(direction: str = "down", amount: int = 3) -> str:
    """Scroll the current browser page."""
    try:
        import pyautogui
        key = "pagedown" if direction == "down" else "pageup"
        for _ in range(amount):
            pyautogui.press(key)
            time.sleep(0.1)
        return f"Scrolled {direction}, sir."
    except Exception as e:
        return f"Couldn't scroll: {e}"


# ── Command parser ─────────────────────────────────────────────────────────────

def handle_browser_command(original: str, text: str) -> str | None:
    """
    Try to handle a browser-related command.
    Returns a response string if handled, None if not a browser command.
    """
    # YouTube play/search
    yt_play = re.search(
        r'(?:play|watch|put on)\s+(.+?)\s+(?:on|in)\s+youtube', text
    )
    if yt_play:
        return youtube_play(yt_play.group(1).strip())

    yt_search = re.search(r'(?:search|find|look up)\s+(.+?)\s+on youtube', text)
    if yt_search:
        return youtube_search(yt_search.group(1).strip())

    if "youtube" in text:
        query_match = re.search(r'youtube\s+(?:for\s+)?(.+)', text)
        if query_match:
            return youtube_search(query_match.group(1).strip())
        webbrowser.open("https://www.youtube.com")
        return "🎬 Opening YouTube, sir."

    # Google search
    google_match = re.search(r'google\s+(?:search\s+)?(?:for\s+)?(.+)', text)
    if google_match:
        return google_search(google_match.group(1).strip())

    # Spotify
    spotify_match = re.search(r'spotify\s+(?:for\s+|play\s+)?(.+)', text)
    if spotify_match and "open" not in text[:10]:
        return open_spotify_web(spotify_match.group(1).strip())
    if "spotify" in text:
        return open_spotify_web()

    # Specific sites
    if "netflix" in text:
        return open_netflix()
    if "gmail" in text or "email" in text or "open mail" in text:
        return open_gmail()
    if "whatsapp" in text:
        return open_whatsapp_web()
    if "chatgpt" in text or "chat gpt" in text:
        return open_chatgpt()
    if "maps" in text or "directions to" in text or "navigate to" in text:
        loc_match = re.search(r'(?:maps|directions to|navigate to)\s+(.+)', text)
        location = loc_match.group(1).strip() if loc_match else ""
        return open_google_maps(location)

    # Tab management
    if "close tab" in text or "close this tab" in text:
        return close_browser_tab()
    if "new tab" in text:
        url_match = re.search(r'new tab\s+(?:and\s+open\s+)?(.+)', text)
        return new_browser_tab(url_match.group(1).strip() if url_match else "")

    # Scroll
    if "scroll down" in text:
        return scroll_page("down")
    if "scroll up" in text:
        return scroll_page("up")

    return None
