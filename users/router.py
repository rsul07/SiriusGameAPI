import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from auth.dependencies import get_current_user
from config import AVATAR_DIR
from db.users import UserOrm
from events.repository import EventRepository
from events.schemas import SParticipationOut
from users.repository import UserRepository
from users.schemas import SUserOut, SUserUpdate, SPasswordUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=SUserOut)
async def read_users_me(current_user: UserOrm = Depends(get_current_user)):
    """Возвращает данные текущего авторизованного пользователя."""
    return current_user


@router.get("/me/participations", response_model=list[SParticipationOut])
async def read_my_participations(current_user: UserOrm = Depends(get_current_user)):
    """Возвращает список мероприятий, в которых участвует текущий пользователь."""
    return await EventRepository.get_participations_for_user(current_user.id)


@router.patch("/me", response_model=SUserOut)
async def update_users_me(
        user_data: SUserUpdate,
        current_user: UserOrm = Depends(get_current_user)
):
    """Обновляет данные текущего пользователя (рост, вес и т.д.)."""
    updated_user = await UserRepository.update_user(current_user.id, user_data)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated_user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_password(
        password_data: SPasswordUpdate,
        current_user: UserOrm = Depends(get_current_user),
):
    """Эндпоинт для смены пароля."""
    success = await UserRepository.update_password(
        current_user.id, password_data.old_password, password_data.new_password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный старый пароль.",
        )


@router.post("/me/avatar", response_model=SUserOut)
async def update_user_avatar(
        file: UploadFile = File(...),
        current_user: UserOrm = Depends(get_current_user),
):
    """Загрузка/замена аватара пользователя."""

    # 1. Удаляем старый файл, если был
    if current_user.avatar_url:
        old_path = Path(current_user.avatar_url.lstrip("/"))
        try:
            if old_path.exists():
                old_path.unlink()
        except OSError as e:
            print(f"Error deleting old avatar: {e}")

    # 2. Сохраняем новый
    new_name = f"{current_user.id}{Path(file.filename).suffix}"
    new_path = AVATAR_DIR / new_name

    print("SAVED AVATAR TO:", new_path)

    with new_path.open("wb") as buf:
        shutil.copyfileobj(file.file, buf)

    # 3. Записываем URL
    avatar_url = f"/media/avatars/{new_name}"
    updated_user = await UserRepository.update_user(
        current_user.id,
        SUserUpdate(avatar_url=avatar_url)
    )
    return updated_user
