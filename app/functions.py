from datetime import datetime
from typing import Dict, List, Optional

import requests

# Weather codes from Open-Meteo (https://open-meteo.com/)
WEATHER_CODE_MAP = {
    0: ("Ясно", "sunny"),
    1: ("В основном ясно", "sunny"),
    2: ("Переменная облачность", "cloudy"),
    3: ("Пасмурно", "cloudy"),
    45: ("Туман", "fog"),
    48: ("Туман", "fog"),
    51: ("Морось", "rain"),
    53: ("Морось", "rain"),
    55: ("Морось", "rain"),
    56: ("Ледяная морось", "rain"),
    57: ("Ледяная морось", "rain"),
    61: ("Лёгкий дождь", "rain"),
    63: ("Дождь", "rain"),
    65: ("Сильный дождь", "rain"),
    66: ("Ледяной дождь", "rain"),
    67: ("Ледяной дождь", "rain"),
    71: ("Небольшой снег", "snow"),
    73: ("Снег", "snow"),
    75: ("Сильный снег", "snow"),
    77: ("Снег с крупой", "snow"),
    80: ("Небольшие ливни", "rain"),
    81: ("Ливень", "rain"),
    82: ("Сильный ливень", "rain"),
    85: ("Снег", "snow"),
    86: ("Сильный снег", "snow"),
    95: ("Гроза", "storm"),
    96: ("Гроза с градом", "storm"),
    99: ("Гроза с градом", "storm"),
}


def _normalize_weather_code(code: int) -> Dict[str, str]:
    description, icon = WEATHER_CODE_MAP.get(code, ("Неизвестно", "cloudy"))
    return {"description": description, "icon": icon}


def _find_humidity(hourly: Dict, current_time: str) -> Optional[float]:
    times = hourly.get("time", [])
    humidity = hourly.get("relativehumidity_2m") or hourly.get("relative_humidity_2m")
    if not times or not humidity:
        return None
    try:
        idx = times.index(current_time)
        return float(humidity[idx])
    except ValueError:
        # Если точное время не найдено, берём ближайшее значение (первое доступное)
        if humidity and len(humidity) > 0:
            return float(humidity[0])
        return None


def fetch_weather(city: str) -> Dict:
    """Fetch current weather and 5-day forecast for a city using Open-Meteo."""
    city = city.strip()
    if not city:
        raise ValueError("Город не задан")

    geo_resp = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "ru", "format": "json"},
        timeout=10,
    )
    geo_resp.raise_for_status()
    geo_data = geo_resp.json()
    results = geo_data.get("results", [])
    if not results:
        raise ValueError("Город не найден")

    location = results[0]
    latitude = location["latitude"]
    longitude = location["longitude"]
    resolved_name = location.get("name", city)

    forecast_resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true",
            "hourly": "relativehumidity_2m",
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,windspeed_10m_max",
            "timezone": "auto",
        },
        timeout=10,
    )
    forecast_resp.raise_for_status()
    data = forecast_resp.json()

    current_raw = data.get("current_weather", {})
    current_time = current_raw.get("time")
    humidity = _find_humidity(data.get("hourly", {}), current_time) if current_time else None
    
    # Если влажность не найдена по точному времени, берём ближайшее значение из hourly
    if humidity is None:
        hourly_data = data.get("hourly", {})
        humidity_values = hourly_data.get("relativehumidity_2m") or hourly_data.get("relative_humidity_2m")
        if humidity_values and len(humidity_values) > 0:
            # Берём первое доступное значение (текущее или ближайшее)
            humidity = float(humidity_values[0])
    
    current_code = int(current_raw.get("weathercode", 0))
    current = {
        "temperature": current_raw.get("temperature"),
        "wind_speed": current_raw.get("windspeed"),
        "humidity": humidity,
        **_normalize_weather_code(current_code),
    }

    daily = data.get("daily", {})
    forecast: List[Dict] = []
    dates = daily.get("time", [])[:5]
    codes = daily.get("weathercode", [])[:5]
    max_t = daily.get("temperature_2m_max", [])[:5]
    min_t = daily.get("temperature_2m_min", [])[:5]
    wind_max = daily.get("windspeed_10m_max", [])[:5]

    for idx, day in enumerate(dates):
        code = int(codes[idx]) if idx < len(codes) else 0
        description = _normalize_weather_code(code)
        forecast.append(
            {
                "date": datetime.fromisoformat(day).date(),
                "temp_max": max_t[idx] if idx < len(max_t) else None,
                "temp_min": min_t[idx] if idx < len(min_t) else None,
                "wind_speed": wind_max[idx] if idx < len(wind_max) else None,
                **description,
            }
        )

    return {
        "city": resolved_name,
        "current": current,
        "forecast": forecast,
    }

