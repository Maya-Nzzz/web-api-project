from typing import Tuple, Dict, Any, Optional
import asyncio
import random

import httpx


CITY_COORDS: Dict[str, Tuple[float, float]] = {
    "Yekaterinburg": (56.8389, 60.6057),
    "Moscow": (55.7558, 37.6173),
    "Saint Petersburg": (59.9386, 30.3141),
}


def _backoff_seconds(attempt: int) -> float:
    base = 0.6 * (2 ** (attempt - 1))
    jitter = random.uniform(0.0, 0.35)
    return min(base + jitter, 4.0)


async def fetch_current_weather(
    city: str,
    *,
    retries: int = 3,
    timeout_total: float = 15.0,
) -> Dict[str, Any]:

    if city not in CITY_COORDS:
        raise ValueError(f"Неизвестный город: {city}.")

    lat, lon = CITY_COORDS[city]
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m",
        "timezone": "UTC",
    }

    timeout = httpx.Timeout(timeout_total, connect=6.0)

    last_error: Optional[Exception] = None

    for attempt in range(1, retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.get(url, params=params)

            if 500 <= r.status_code <= 599:
                raise httpx.HTTPStatusError(
                    f"Ошибка сервера {r.status_code}",
                    request=r.request,
                    response=r,
                )

            r.raise_for_status()
            data = r.json()

            cur = data.get("current") or {}
            temperature = cur.get("temperature_2m")
            wind_speed = cur.get("wind_speed_10m")

            return {
                "city": city,
                "temperature": float(temperature) if temperature is not None else None,
                "wind_speed": float(wind_speed) if wind_speed is not None else None,
                "raw": data,
            }

        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError, httpx.RemoteProtocolError, httpx.HTTPStatusError) as e:
            last_error = e
            if attempt == retries:
                break

            sleep_s = _backoff_seconds(attempt)
            print(f"[погода] {city}: Попытка {attempt}/{retries} провалена: {type(e).__name__}. Попробовать снова через {sleep_s:.2f}с")
            await asyncio.sleep(sleep_s)

        except Exception as e:
            raise

    raise RuntimeError(f"Ошибка соединения для {city} после {retries} попыток: {last_error!r}")
