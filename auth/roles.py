from fastapi import Depends, HTTPException, status
from auth.dependencies import get_current_user
from db.users import UserOrm, RoleEnum


def require_role(required_role: RoleEnum):
    """
    Фабрика зависимостей для проверки конкретной роли.
    """

    def dependency(current_user: UserOrm = Depends(get_current_user)) -> UserOrm:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user

    return dependency


def require_organizer_or_admin(current_user: UserOrm = Depends(get_current_user)) -> UserOrm:
    """
    Зависимость, которая разрешает доступ организаторам И администраторам.
    """
    print("ВЫЗОВ get_current_user. ЗАЩИТА АКТИВНА")
    if current_user.role not in [RoleEnum.organizer, RoleEnum.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
