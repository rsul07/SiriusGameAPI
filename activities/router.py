from fastapi import APIRouter, HTTPException

from events.schemas import SActivityOut, SActivityUpdate, SActivityAdd
from .repository import ActivityRepository

events_router = APIRouter(prefix="/events/{event_id}/activities", tags=["Activities"])
activities_router = APIRouter(prefix="/activities", tags=["Activities"])


@events_router.get("", response_model=list[SActivityOut])
async def get_activities_for_event(event_id: int):
    return await ActivityRepository.get_by_event_id(event_id)


@events_router.post("", response_model=dict)
async def add_activity_to_event(event_id: int, data: SActivityAdd):
    try:
        activity_id = await ActivityRepository.add_one(event_id, data)
        if not activity_id:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"ok": True, "activity_id": activity_id}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@activities_router.patch("/{activity_id}", response_model=dict)
async def edit_activity(activity_id: int, data: SActivityUpdate):
    if not await ActivityRepository.edit_one(activity_id, data):
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"ok": True}


@activities_router.delete("/{activity_id}", response_model=dict)
async def delete_activity(activity_id: int):
    if not await ActivityRepository.delete_one(activity_id):
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"ok": True}
