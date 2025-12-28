import asyncio
import json
from nats.aio.client import Client as NATS

NATS_URL = "nats://127.0.0.1:4222"
SUBJECT = "items.updates"

async def main():
    nc = NATS()
    await nc.connect(servers=[NATS_URL])
    print(f"[pub] подключение {NATS_URL}")

    payload = {
        "event": "external_weather",
        "item": {"city": "Moscow", "temperature": 0.0, "wind_speed": 2.0},
        "meta": {"source": "external_script"},
    }

    await nc.publish(SUBJECT, json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    await nc.flush()
    print("[pub] published:", payload)
    await nc.close()

if __name__ == "__main__":
    asyncio.run(main())
