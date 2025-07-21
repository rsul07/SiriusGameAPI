from hmac import new
import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from auth.dependencies import get_current_user
from db import new_session
from db.events import EventParticipationOrm
from db.users import UserOrm
from events.repository import EventRepository
from events.schemas import SParticipationOut

from config import AVATAR_DIR

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


@router.post("/{participation_id}/avatar", response_model=SParticipationOut)
async def update_team_avatar(
        participation_id: int,
        file: UploadFile = File(...),
        current_user: UserOrm = Depends(get_current_user),
):
    """
    Загружает аватар для команды. Доступно только капитану.
    """
    async with new_session() as session:
        # 1. Получаем участие и проверяем права
        participation = await session.get(EventParticipationOrm, participation_id)
        if not participation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Команда не найдена.")
        if participation.creator_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Только капитан может менять аватар команды.")

        # 2. Удаляем старый аватар, если он есть
        if participation.team_avatar_url:
            old_avatar_path = Path(participation.team_avatar_url.lstrip("/"))
            if old_avatar_path.exists():
                old_avatar_path.unlink()

        # 3. Сохраняем новый файл
        file_extension = Path(file.filename).suffix
        new_filename = f"{participation_id}{file_extension}"
        file_path = AVATAR_DIR / new_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 4. Обновляем путь в БД
        participation.team_avatar_url = f"/media/avatars/{new_filename}"
        await session.commit()
        await session.refresh(participation)

        # Подгружаем связанные данные для корректного ответа
        full_participation = await EventRepository.get_participation_by_id(participation_id)
        return full_participation
