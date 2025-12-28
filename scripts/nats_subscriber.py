import asyncio
import json
from nats.aio.client import Client as NATS

NATS_URL = "nats://127.0.0.1:4222"
SUBJECT = "items.updates"

async def main():
    nc = NATS()
    await nc.connect(servers=[NATS_URL])
    print(f"[sub] подключение {NATS_URL}, subject={SUBJECT}")

    async def cb(msg):
        payload = json.loads(msg.data.decode("utf-8"))
        print("[sub] got:", payload)

    await nc.subscribe(SUBJECT, cb=cb)

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
