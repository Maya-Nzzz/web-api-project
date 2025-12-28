from fastapi import FastAPI

from app.config import settings
from app.api.items import router as items_router
from app.api.tasks import router as tasks_router
from app.ws.router import router as ws_router

from app.db.database import engine
from app.models.item import Base
from app.tasks.runner import runner
from app.nats.client import nats_client


app = FastAPI(title=settings.app_title, version="0.5.0")


@app.get("/ping")
async def ping():
    return {"message": "pong"}


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await nats_client.connect()

    await runner.start()


@app.on_event("shutdown")
async def on_shutdown():
    await runner.stop()
    await nats_client.close()


app.include_router(items_router)
app.include_router(tasks_router)
app.include_router(ws_router)
