from fastapi import APIRouter, Depends, HTTPException, status
import uuid

from auth.dependencies import get_current_user
from db.users import UserOrm
from events.repository import EventRepository

router = APIRouter(prefix="/participations", tags=["Participations"])


@router.post("/{participation_id}/join", status_code=status.HTTP_204_NO_CONTENT)
async def join_team(
        participation_id: int,
        current_user: UserOrm = Depends(get_current_user),
):
    """Присоединиться к существующей команде."""
    try:
        await EventRepository.add_member_to_participation(participation_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{participation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_participation(
        participation_id: int,
        current_user: UserOrm = Depends(get_current_user),
):
    """Удалить свое участие или команду (только для создателя)."""
    try:
        await EventRepository.delete_participation(participation_id, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{participation_id}/members/{user_id_to_remove}", status_code=status.HTTP_204_NO_CONTENT)
async def leave_or_kick_member(
        participation_id: int,
        user_id_to_remove: uuid.UUID,
        current_user: UserOrm = Depends(get_current_user),
):
    """Покинуть команду или исключить участника (только для капитана)."""
    try:
        await EventRepository.remove_member_from_participation(
            participation_id, user_id_to_remove, current_user.id
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{participation_id}/transfer-captaincy/{new_captain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def transfer_captaincy(
        participation_id: int,
        new_captain_id: uuid.UUID,
        current_user: UserOrm = Depends(get_current_user),
):
    """Передать права капитана другому участнику."""
    try:
        await EventRepository.transfer_captaincy(
            participation_id, new_captain_id, current_user.id
        )
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
