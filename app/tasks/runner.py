import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import AsyncSessionLocal
from app.models.item import ItemDB
from app.services.weather import fetch_current_weather
from app.ws.manager import manager
from app.nats.client import nats_client


class BackgroundRunner:
    def __init__(self) -> None:
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except Exception:
                pass

    async def _loop(self) -> None:
        await asyncio.sleep(1)
        while not self._stop_event.is_set():
            try:
                await self.run_once(city="Yekaterinburg", source="background")
            except Exception as e:
                print("[Фоновый исполнитель] ошибка:", repr(e))
            await asyncio.sleep(settings.background_period_seconds)

    async def run_once(self, city: str, source: str = "manual") -> ItemDB:
        async with self._lock:
            weather = await fetch_current_weather(city)

            async with AsyncSessionLocal() as session:
                item = await self._save_item(session, weather)

            payload = {
                "event": "created_external" if source != "manual" else "created_external_manual",
                "item": {
                    "id": item.id,
                    "city": item.city,
                    "temperature": item.temperature,
                    "wind_speed": item.wind_speed,
                    "created_at": item.created_at,
                },
                "meta": {"source": source},
            }

            published = await nats_client.publish_event(payload)
            if not published:
                await manager.broadcast(payload)

            return item

    async def _save_item(self, session: AsyncSession, weather: dict) -> ItemDB:
        item = ItemDB(
            city=weather["city"],
            temperature=weather["temperature"],
            wind_speed=weather["wind_speed"],
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item


runner = BackgroundRunner()
