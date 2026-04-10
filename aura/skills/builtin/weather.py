"""Weather skill - Get weather forecasts."""

import httpx
from aura.skills import Skill


class WeatherSkill(Skill):
    """Get weather using wttr.in or Open-Meteo."""

    name = "weather"
    description = "Get current weather and forecasts"
    commands = ["weather", "forecast", "rain"]

    def run(self, command: str, args: dict = None) -> str:
        args = args or {}
        city = args.get("city", "")

        if not city:
            return "Please specify a city. Usage: weather <city>"

        return self._get_weather(city)

    def _get_weather(self, city: str) -> str:
        """Get weather from wttr.in."""
        try:
            url = f"https://wttr.in/{city}?format=j1"
            response = httpx.get(url, timeout=10)
            data = response.json()

            current = data.get("current_condition", [{}])[0]
            temp = current.get("temp_C", "N/A")
            condition = current.get("weatherDesc", [{}])[0].get("value", "N/A")
            humidity = current.get("humidity", "N/A")
            wind = current.get("windspeedKmph", "N/A")

            return (
                f"Weather in {city}:\n"
                f"🌡️ Temperature: {temp}°C\n"
                f"☁️ Condition: {condition}\n"
                f"💧 Humidity: {humidity}%\n"
                f"💨 Wind: {wind} km/h"
            )
        except Exception as e:
            return f"Error getting weather: {e}"


skill = WeatherSkill()
