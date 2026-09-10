"""
weather.py — JARVIS Weather Intelligence
=========================================
Gets real weather data with no API key using wttr.in.
Supports current conditions, forecasts, and location-based queries.
"""

import requests
import json


def get_weather(location: str = "") -> str:
    """
    Fetch current weather for a location.
    Defaults to auto-detected location if none provided.

    Args:
        location: City name (e.g. "Mumbai") or leave empty for auto-detect

    Returns:
        JARVIS-style weather report
    """
    loc = location.strip().replace(" ", "+") if location.strip() else ""
    try:
        # wttr.in JSON API — completely free, no key needed
        url = f"https://wttr.in/{loc}?format=j1"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "JARVIS/1.0"})
        resp.raise_for_status()
        data = resp.json()

        current = data["current_condition"][0]
        area    = data["nearest_area"][0]

        city    = area["areaName"][0]["value"]
        country = area["country"][0]["value"]

        temp_c  = current["temp_C"]
        temp_f  = current["temp_F"]
        feels_c = current["FeelsLikeC"]
        desc    = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]
        wind_kmph = current["windspeedKmph"]
        wind_dir = current["winddir16Point"]
        visibility = current["visibility"]

        # Forecast
        forecast_lines = []
        for day in data["weather"][:3]:
            date = day["date"]
            max_c = day["maxtempC"]
            min_c = day["mintempC"]
            desc_day = day["hourly"][4]["weatherDesc"][0]["value"]   # midday
            forecast_lines.append(f"  • {date}: {desc_day}, {min_c}°–{max_c}°C")

        forecast_str = "\n".join(forecast_lines)

        return (
            f"🌤️ **Weather Report — {city}, {country}**\n\n"
            f"**Current:** {desc}\n"
            f"**Temperature:** {temp_c}°C ({temp_f}°F), feels like {feels_c}°C\n"
            f"**Humidity:** {humidity}%  |  **Wind:** {wind_kmph} km/h {wind_dir}\n"
            f"**Visibility:** {visibility} km\n\n"
            f"**3-Day Forecast:**\n{forecast_str}"
        )

    except requests.exceptions.ConnectionError:
        return "No internet connection to fetch weather, sir."
    except requests.exceptions.Timeout:
        return "Weather service timed out, sir. Try again."
    except Exception as e:
        return f"Couldn't fetch weather data: {e}"


def get_weather_brief(location: str = "") -> str:
    """One-line weather summary for voice output."""
    loc = location.strip().replace(" ", "+") if location.strip() else ""
    try:
        url = f"https://wttr.in/{loc}?format=3"
        resp = requests.get(url, timeout=8, headers={"User-Agent": "JARVIS/1.0"})
        resp.raise_for_status()
        return f"🌤️ {resp.text.strip()}"
    except Exception:
        return get_weather(location)
