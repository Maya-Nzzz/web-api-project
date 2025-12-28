from typing import List

from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder


class ConnectionManager:
    def __init__(self) -> None:
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, message: dict) -> None:
        payload = jsonable_encoder(message) # для корректной сериализации дат
        for ws in list(self.active):
            try:
                await ws.send_json(payload)
            except Exception as e:
                print("[WS] send error:", repr(e))
                self.disconnect(ws)


manager = ConnectionManager()
