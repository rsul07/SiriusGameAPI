from fastapi import APIRouter, Depends, HTTPException, status
from users.schemas import SUserOut, SUserUpdate
from auth.dependencies import get_current_user
from db.users import UserOrm
from users.repository import UserRepository

router = APIRouter(prefix="/users", tags=["Users"])


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
