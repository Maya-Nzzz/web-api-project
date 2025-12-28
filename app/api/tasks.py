from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.tasks.runner import runner


router = APIRouter(prefix="/tasks", tags=["tasks"])


class RunRequest(BaseModel):
    city: Optional[str] = "Yekaterinburg"


@router.post("/run")
async def run_background_task(req: RunRequest):
    try:
        item = await runner.run_once(city=req.city or "Yekaterinburg", source="manual")
        return {
            "status": "ok",
            "saved_item_id": item.id,
            "city": item.city,
            "temperature": item.temperature,
            "wind_speed": item.wind_speed,
            "created_at": item.created_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")
