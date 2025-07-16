from fastapi import APIRouter, HTTPException, Depends
from starlette import status

from auth.dependencies import get_current_user
from db.users import UserOrm, RoleEnum
from events.repository import EventRepository
from events.schemas import SEventAdd, SEvent, SEventId, SEventUpdate, SEventMediaAdd, SEventCard, SMediaReorderItem, \
    SParticipationOut, SParticipationCreate, SJudgeAdd
from auth.roles import require_organizer_or_admin

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=list[SEventCard])
async def get_events():
    return await EventRepository.get_all()


@router.get("/{event_id}", response_model=SEvent)
async def get_event(event_id: int):
    event = await EventRepository.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("", response_model=SEventId)
async def add_event(event: SEventAdd,
                    user: UserOrm = Depends(require_organizer_or_admin)):
    event_id = await EventRepository.add_one(event)
    return {"ok": True, "event_id": event_id}


@router.patch("/{event_id}", response_model=dict)
async def edit_event(event_id: int,
                     data: SEventUpdate,
                     user: UserOrm = Depends(require_organizer_or_admin)):
    try:
        updated = await EventRepository.edit(event_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="Event not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"ok": True}


@router.delete("/{event_id}", response_model=dict)
async def delete_event(event_id: int,
                       user: UserOrm = Depends(require_organizer_or_admin)):
    deleted = await EventRepository.delete(event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"ok": True}


@router.post("/{event_id}/media", response_model=dict)
async def add_event_media(event_id: int,
                          body: SEventMediaAdd,
                          user: UserOrm = Depends(require_organizer_or_admin)):
    iid = await EventRepository.add_media(event_id, body)
    if iid is None:
        raise HTTPException(404, "Event not found")
    return {"ok": True, "media_id": iid}


@router.delete("/{event_id}/media/{media_id}", response_model=dict)
async def delete_event_media(event_id: int,
                             media_id: int,
                             user: UserOrm = Depends(require_organizer_or_admin)):
    deleted = await EventRepository.delete_media(event_id, media_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="media not found")
    return {"ok": True}


@router.patch("/{event_id}/media/reorder", response_model=dict)
async def reorder_media(event_id: int,
                        body: list[SMediaReorderItem],
                        user: UserOrm = Depends(require_organizer_or_admin)):
    try:
        ok = await EventRepository.reorder_media(event_id, body)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not ok:
        raise HTTPException(404, "Event not found or empty body")
    return {"ok": True}


@router.post(
    "/{event_id}/participate",
    response_model=SParticipationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_participation(
        event_id: int,
        participation_data: SParticipationCreate,
        current_user: UserOrm = Depends(get_current_user),
):
    """
    Создает участие в мероприятии (личное или командное).
    """
    try:
        participation = await EventRepository.add_participation(
            event_id, current_user.id, participation_data
        )
        full_participation = await EventRepository.get_participation_by_id(participation.id)
        return full_participation
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/{event_id}/participations",
    response_model=list[SParticipationOut],
)
async def get_event_participations(event_id: int):
    """
    Возвращает список всех команд и участников мероприятия.
    """
    return await EventRepository.get_participations_for_event(event_id)


@router.post("/{event_id}/judges", status_code=status.HTTP_201_CREATED)
async def add_judge(
        event_id: int,
        judge_data: SJudgeAdd,
        current_user: UserOrm = Depends(get_current_user)
):
    if current_user.role not in [RoleEnum.admin, RoleEnum.organizer]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав для назначения судей.")

    try:
        await EventRepository.add_judge_to_event(event_id, judge_data)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))