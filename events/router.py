from fastapi import APIRouter, HTTPException, Depends
from events.repository import EventRepository
from events.schemas import SEventAdd, SEvent, SEventId, SEventUpdate
from typing import Annotated

router = APIRouter(prefix="/events", tags=["events"])

@router.get("", response_model=list[SEvent])
async def get_events():
    return await EventRepository.get_all()

@router.post("", response_model=SEventId)
async def add_event(event: Annotated[SEventAdd, Depends()]):
    event_id = await EventRepository.add_one(event)
    return {"ok": True, "event_id": event_id}

@router.patch("/{event_id}", response_model=dict)
async def edit_event(event_id: int, data: Annotated[SEventUpdate, Depends()]):
    updated = await EventRepository.edit(event_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"ok": True}

@router.delete("/{event_id}", response_model=dict)
async def delete_event(event_id: int):
    deleted = await EventRepository.delete(event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"ok": True}