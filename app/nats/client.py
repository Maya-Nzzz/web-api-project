import json
from typing import Any, Dict, Optional

from nats.aio.client import Client as NATS
from nats.aio.errors import ErrNoServers

from app.config import settings
from app.ws.manager import manager
from app.db.database import AsyncSessionLocal
from app.models.item import ItemDB


class NATSClient:
    def __init__(self) -> None:
        self.nc = NATS()
        self._sub_sid: Optional[int] = None

    @property
    def is_connected(self) -> bool:
        return bool(self.nc.is_connected)

    async def connect(self) -> None:
        try:
            await self.nc.connect(servers=[settings.nats_url], name="web-api-project")
            self._sub_sid = await self.nc.subscribe(settings.nats_subject, cb=self._on_message)
            print(f"[NATS] подключено к {settings.nats_url}, подписка оформлена на: {settings.nats_subject}")
        except ErrNoServers:
            print(f"[NATS] серверы по адресу {settings.nats_url} не найдены. Запустите NATS (docker compose up -d).")

    async def close(self) -> None:
        try:
            if self.nc.is_connected:
                await self.nc.drain()
                await self.nc.close()
                print("[NATS] закрыто")
        except Exception as e:
            print("[NATS] ошибка при закрытии:", repr(e))

    async def publish_event(self, payload: Dict[str, Any]) -> bool:
        """
        Возвращает True если сообщение ушло в NATS, иначе False.
        """
        if not self.nc.is_connected:
            return False

        data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        await self.nc.publish(settings.nats_subject, data)
        return True

    async def _on_message(self, msg) -> None:
        """
        При получении сообщения: логируем, пересылаем в WebSockets
        """
        try:
            raw = msg.data.decode("utf-8")
            payload = json.loads(raw)
        except Exception as e:
            print("[NATS] ошибка:", repr(e))
            return

        print(f"[NATS] recv {msg.subject}: {payload.get('event')}")

        if payload.get("event") == "external_weather":
            item = payload.get("item") or {}
            await self._save_item_from_nats(item)

        await manager.broadcast({
            "event": "nats_received",
            "payload": payload,
        })

    async def _save_item_from_nats(self, item: Dict[str, Any]) -> None:
        city = item.get("city")
        temperature = item.get("temperature")
        wind_speed = item.get("wind_speed")

        if city is None or temperature is None:
            print("[NATS] отсутствующие поля external_weather")
            return

        async with AsyncSessionLocal() as session:
            db_item = ItemDB(
                city=str(city),
                temperature=float(temperature),
                wind_speed=float(wind_speed) if wind_speed is not None else None,
            )
            session.add(db_item)
            await session.commit()
            await session.refresh(db_item)

        await manager.broadcast({
            "event": "created_from_nats",
            "item": {
                "id": db_item.id,
                "city": db_item.city,
                "temperature": db_item.temperature,
                "wind_speed": db_item.wind_speed,
                "created_at": db_item.created_at,
            }
        })


nats_client = NATSClient()
