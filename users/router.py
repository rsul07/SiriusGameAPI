import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from users.schemas import SUserOut, SUserUpdate, SPasswordUpdate
from auth.dependencies import get_current_user
from db.users import UserOrm
from users.repository import UserRepository
import shutil

router = APIRouter(prefix="/users", tags=["Users"])
Path("media/avatars").mkdir(parents=True, exist_ok=True)


@router.get("/me", response_model=SUserOut)
async def read_users_me(current_user: UserOrm = Depends(get_current_user)):
    """Возвращает данные текущего авторизованного пользователя."""
    return current_user


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
    """Эндпоинт для загрузки аватара."""

    if current_user.avatar_url:
        old_avatar_path = current_user.avatar_url.lstrip('/')
        if os.path.exists(old_avatar_path):
            try:
                os.remove(old_avatar_path)
            except OSError as e:
                print(f"Error deleting old avatar: {e}")

    file_extension = Path(file.filename).suffix
    new_filename = f"{current_user.id}{file_extension}"
    file_path = f"media/avatars/{new_filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    avatar_url = f"/{file_path}"
    updated_user = await UserRepository.update_user(
        current_user.id, SUserUpdate(avatar_url=avatar_url)
    )
    return updated_user
