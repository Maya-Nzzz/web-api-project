from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.models.item import ItemDB
from app.ws.manager import manager
from app.nats.client import nats_client


router = APIRouter(prefix="/items", tags=["items"])


class ItemBase(BaseModel):
    city: str
    temperature: float
    wind_speed: Optional[float] = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    city: Optional[str] = None
    temperature: Optional[float] = None
    wind_speed: Optional[float] = None


class Item(ItemBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=List[Item])
async def list_items(session: AsyncSession = Depends(get_session)) -> List[Item]:
    stmt = select(ItemDB).order_by(ItemDB.id)
    res = await session.execute(stmt)
    return res.scalars().all()


@router.get("/{item_id}", response_model=Item)
async def get_item(item_id: int, session: AsyncSession = Depends(get_session)) -> Item:
    item = await session.get(ItemDB, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("", response_model=Item, status_code=201)
async def create_item(data: ItemCreate, session: AsyncSession = Depends(get_session)) -> Item:
    item = ItemDB(**data.model_dump())
    session.add(item)
    await session.commit()
    await session.refresh(item)

    payload = {
        "event": "created",
        "item": Item.model_validate(item).model_dump(mode="json"),
        "meta": {"source": "rest"},
    }

    published = await nats_client.publish_event(payload)
    if not published:
        # если NATS не поднят — всё равно уведомим WS
        await manager.broadcast(payload)

    return item


@router.patch("/{item_id}", response_model=Item)
async def update_item(item_id: int, data: ItemUpdate, session: AsyncSession = Depends(get_session)) -> Item:
    item = await session.get(ItemDB, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    upd = data.model_dump(exclude_unset=True)
    for k, v in upd.items():
        setattr(item, k, v)

    await session.commit()
    await session.refresh(item)

    payload = {
        "event": "updated",
        "item": Item.model_validate(item).model_dump(mode="json"),
        "meta": {"source": "rest"},
    }

    published = await nats_client.publish_event(payload)
    if not published:
        await manager.broadcast(payload)

    return item


@router.delete("/{item_id}")
async def delete_item(item_id: int, session: AsyncSession = Depends(get_session)):
    item = await session.get(ItemDB, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await session.delete(item)
    await session.commit()

    payload = {
        "event": "deleted",
        "item_id": item_id,
        "meta": {"source": "rest"},
    }

    published = await nats_client.publish_event(payload)
    if not published:
        await manager.broadcast(payload)

    return {"status": "deleted"}
