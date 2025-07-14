import random
import string

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db import new_session
from db.users import UserOrm
from users.schemas import SUserRegister
from auth.security import get_password_hash
from auth.exceptions import UserAlreadyExistsError


async def generate_unique_handle(session: AsyncSession) -> str:
    """
    Генерирует уникальный handle, используя переданную сессию.
    """

    for _ in range(20):
        handle = "".join(random.choices(string.digits, k=10))

        existing_user = await session.execute(
            select(UserOrm).where(UserOrm.handle == handle)
        )
        if not existing_user.scalar_one_or_none():
            return handle

    raise RuntimeError("Could not generate a unique handle after 20 attempts.")


class UserRepository:
    @classmethod
    async def create_user(cls, data: SUserRegister) -> UserOrm:
        """
        Создает нового пользователя. Ловит ошибку уникальности от БД.
        """
        async with new_session() as session:
            try:
                user_dict = data.model_dump()
                user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
                user_dict["handle"] = await generate_unique_handle(session)

                new_user = UserOrm(**user_dict)
                session.add(new_user)
                await session.flush()
                await session.commit()
                return new_user
            except IntegrityError as e:
                await session.rollback()
                raise UserAlreadyExistsError from e

    @classmethod
    async def get_user_by_email(cls, email: str) -> UserOrm | None:
        """Находит пользователя по email."""
        async with new_session() as session:
            query = select(UserOrm).where(UserOrm.email == email)
            result = await session.execute(query)
            return result.scalar_one_or_none()
