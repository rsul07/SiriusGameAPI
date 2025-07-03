from fastapi import APIRouter, HTTPException
from events.repository import EventRepository
from events.schemas import SEventAdd, SEvent, SEventId, SEventUpdate, SEventImageAdd

router = APIRouter(prefix="/events", tags=["events"])

@router.get("", response_model=list[SEvent])
async def get_events():
    return await EventRepository.get_all()

@router.post("", response_model=SEventId)
async def add_event(event: SEventAdd):
    event_id = await EventRepository.add_one(event)
    return {"ok": True, "event_id": event_id}

@router.patch("/{event_id}", response_model=dict)
async def edit_event(event_id: int, data: SEventUpdate):
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

@router.post("/{event_id}/image", response_model=dict)
async def add_event_image(event_id: int, body: SEventImageAdd):
    iid = await EventRepository.add_image(event_id, body)
    if iid is None:
        raise HTTPException(404, "Event not found")
    return {"ok": True, "image_id": iid}

@router.delete("/{event_id}/image/{image_id}", response_model=dict)
async def delete_event_image(event_id: int, image_id: int):
    deleted = await EventRepository.delete_image(event_id, image_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"ok": True}