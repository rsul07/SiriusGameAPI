from fastapi import APIRouter, HTTPException
from repository import EventRepository
from schemas import SEventAdd, SEvent, SEventId, SEventUpdate, SEventMediaAdd, SEventCard, SMediaReorderItem, SEventActivityAdd

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[SEventCard])
async def get_events():
    return await EventRepository.get_all()


@router.get("/{event_id}", response_model=SEvent)
async def get_event(event_id: int):
    event = await EventRepository.get_by_id(event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    return event

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


@router.post("/{event_id}/media", response_model=dict)
async def add_event_media(event_id: int, body: SEventMediaAdd):
    iid = await EventRepository.add_media(event_id, body)
    if iid is None:
        raise HTTPException(404, "Event not found")
    return {"ok": True, "media_id": iid}


@router.delete("/{event_id}/media/{media_id}", response_model=dict)
async def delete_event_media(event_id: int, media_id: int):
    deleted = await EventRepository.delete_media(event_id, media_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="media not found")
    return {"ok": True}


@router.post("/{event_id}/activities", response_model=dict)
async def add_event_activity(event_id: int, body: SEventActivityAdd):
    activity_id = await EventRepository.add_activity(event_id, body)
    if activity_id is None:
        raise HTTPException(404, "Event not found")
    return {"ok": True, "activity_id": activity_id}


@router.delete("/{event_id}/activities/{activity_id}", response_model=dict)
async def delete_event_activity(event_id: int, activity_id: int):
    deleted = await EventRepository.delete_activity(event_id, activity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="activity not found")
    return {"ok": True}


@router.patch("/{event_id}/media/reorder", response_model=dict)
async def reorder_media(event_id: int, body: list[SMediaReorderItem]):
    try:
        ok = await EventRepository.reorder_media(event_id, body)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not ok:
        raise HTTPException(404, "Event not found or empty body")
    return {"ok": True}