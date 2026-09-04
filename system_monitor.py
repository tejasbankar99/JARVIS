"""
system_monitor.py — JARVIS Real-Time System Intelligence
=========================================================
Provides live PC health metrics: CPU, RAM, battery, network, disk, GPU.
Used by both the HUD (live panel) and voice commands.
"""

import time
import threading
import psutil
from datetime import datetime

# ── Cache to avoid hammering psutil every call ────────────────────────────────
_cache: dict = {}
_cache_lock = threading.Lock()
_last_update: float = 0
_UPDATE_INTERVAL = 2.0   # seconds


def _refresh():
    """Refresh all system metrics into the cache."""
    global _last_update
    now = time.time()
    if now - _last_update < _UPDATE_INTERVAL:
        return

    net1 = psutil.net_io_counters()
    time.sleep(0.3)
    net2 = psutil.net_io_counters()
    dl = (net2.bytes_recv - net1.bytes_recv) / 0.3 / 1024   # KB/s
    ul = (net2.bytes_sent - net1.bytes_sent) / 0.3 / 1024   # KB/s

    battery = psutil.sensors_battery()

    with _cache_lock:
        _cache["cpu_percent"]    = psutil.cpu_percent(interval=None)
        _cache["cpu_freq"]       = psutil.cpu_freq()
        _cache["cpu_cores"]      = psutil.cpu_count(logical=False)
        _cache["ram"]            = psutil.virtual_memory()
        _cache["disk"]           = psutil.disk_usage("C:\\")
        _cache["net_dl_kbps"]    = dl
        _cache["net_ul_kbps"]    = ul
        _cache["battery"]        = battery
        _cache["boot_time"]      = psutil.boot_time()
        _last_update             = now


def _start_background_refresh():
    """Keep cache warm in the background."""
    def loop():
        while True:
            try:
                _refresh()
            except Exception:
                pass
            time.sleep(_UPDATE_INTERVAL)
    t = threading.Thread(target=loop, daemon=True, name="SysMon")
    t.start()


# ── Public getters ─────────────────────────────────────────────────────────────

def get_all() -> dict:
    """Return the latest cached system metrics dict."""
    _refresh()
    with _cache_lock:
        return dict(_cache)


def get_cpu() -> str:
    """CPU usage as a JARVIS response string."""
    _refresh()
    with _cache_lock:
        pct  = _cache.get("cpu_percent", 0)
        freq = _cache.get("cpu_freq")
        ghz  = f" @ {freq.current/1000:.1f} GHz" if freq else ""
        cores = _cache.get("cpu_cores", "?")
    return f"CPU is at {pct:.0f}%{ghz}, {cores} physical cores, sir."


def get_ram() -> str:
    """RAM usage as a JARVIS response string."""
    _refresh()
    with _cache_lock:
        ram = _cache.get("ram")
    if not ram:
        return "RAM data unavailable, sir."
    used = ram.used / 1e9
    total = ram.total / 1e9
    pct = ram.percent
    return f"RAM: {used:.1f} GB used of {total:.1f} GB ({pct:.0f}%), sir."


def get_battery() -> str:
    """Battery status as a JARVIS response string."""
    _refresh()
    with _cache_lock:
        bat = _cache.get("battery")
    if not bat:
        return "No battery detected — you're on AC power or a desktop, sir."
    plugged = "plugged in" if bat.power_plugged else "on battery"
    mins = bat.secsleft // 60 if bat.secsleft and bat.secsleft > 0 else None
    time_str = f", approximately {mins} minutes remaining" if mins else ""
    return f"Battery at {bat.percent:.0f}% — {plugged}{time_str}, sir."


def get_network() -> str:
    """Network speed as a JARVIS response string."""
    _refresh()
    with _cache_lock:
        dl = _cache.get("net_dl_kbps", 0)
        ul = _cache.get("net_ul_kbps", 0)

    def fmt(kbps):
        return f"{kbps/1024:.1f} MB/s" if kbps > 1024 else f"{kbps:.0f} KB/s"

    return f"Network — Download: {fmt(dl)}, Upload: {fmt(ul)}, sir."


def get_disk() -> str:
    """Disk usage as a JARVIS response string."""
    _refresh()
    with _cache_lock:
        disk = _cache.get("disk")
    if not disk:
        return "Disk data unavailable, sir."
    used = disk.used / 1e9
    total = disk.total / 1e9
    pct = disk.percent
    return f"Drive C: {used:.0f} GB used of {total:.0f} GB ({pct:.0f}% full), sir."


def get_uptime() -> str:
    """System uptime as a JARVIS response string."""
    _refresh()
    with _cache_lock:
        boot = _cache.get("boot_time", time.time())
    uptime_secs = int(time.time() - boot)
    hrs, rem = divmod(uptime_secs, 3600)
    mins = rem // 60
    return f"System has been running for {hrs} hours and {mins} minutes, sir."


def get_full_status() -> str:
    """Full system status report — all metrics combined."""
    _refresh()
    with _cache_lock:
        d = dict(_cache)

    lines = ["⚙️ **JARVIS System Status Report**\n"]

    # CPU
    cpu = d.get("cpu_percent", 0)
    freq = d.get("cpu_freq")
    ghz = f" @ {freq.current/1000:.1f} GHz" if freq else ""
    lines.append(f"🔲 **CPU:** {cpu:.0f}%{ghz}")

    # RAM
    ram = d.get("ram")
    if ram:
        lines.append(f"🧠 **RAM:** {ram.used/1e9:.1f}/{ram.total/1e9:.1f} GB ({ram.percent:.0f}%)")

    # Disk
    disk = d.get("disk")
    if disk:
        lines.append(f"💾 **Disk C:** {disk.used/1e9:.0f}/{disk.total/1e9:.0f} GB ({disk.percent:.0f}%)")

    # Battery
    bat = d.get("battery")
    if bat:
        plugged = "⚡ Charging" if bat.power_plugged else "🔋 Discharging"
        lines.append(f"🔋 **Battery:** {bat.percent:.0f}% — {plugged}")

    # Network
    dl = d.get("net_dl_kbps", 0)
    ul = d.get("net_ul_kbps", 0)
    def fmt(k): return f"{k/1024:.1f} MB/s" if k > 1024 else f"{k:.0f} KB/s"
    lines.append(f"🌐 **Network:** ↓ {fmt(dl)}  ↑ {fmt(ul)}")

    # Uptime
    boot = d.get("boot_time", time.time())
    uptime_secs = int(time.time() - boot)
    hrs, rem = divmod(uptime_secs, 3600)
    mins = rem // 60
    lines.append(f"⏱️ **Uptime:** {hrs}h {mins}m")

    return "\n".join(lines)


def check_battery_alert() -> str | None:
    """Return alert string if battery is critically low, else None."""
    _refresh()
    with _cache_lock:
        bat = _cache.get("battery")
    if bat and not bat.power_plugged:
        if bat.percent <= 10:
            return f"⚠️ CRITICAL: Battery at {bat.percent:.0f}%. Connect power immediately, sir."
        if bat.percent <= 20:
            return f"⚠️ Battery low at {bat.percent:.0f}%. I'd recommend plugging in soon, sir."
    return None


# ── Start background refresh immediately on import ─────────────────────────────
_start_background_refresh()
