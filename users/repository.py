import random
import string
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from db import new_session
from db.users import UserOrm
from users.schemas import SUserRegister
from auth.security import get_password_hash


async def generate_unique_handle(base_name: str) -> str:
    """Генерирует уникальный handle на основе имени."""
    handle_base = "".join(filter(str.isalnum, base_name.lower().replace(" ", "")))[:10]
    async with new_session() as session:
        while True:
            random_suffix = "".join(random.choices(string.digits, k=4))
            handle = f"{handle_base}{random_suffix}"
            if len(handle) > 15: # Ограничение из модели
                handle = handle[:15]

            existing_user = await session.execute(
                select(UserOrm).where(UserOrm.handle == handle)
            )
            if not existing_user.scalar_one_or_none():
                return handle


class UserRepository:
    @classmethod
    async def create_user(cls, data: SUserRegister) -> UserOrm:
        """Создает нового пользователя в базе данных."""
        async with new_session() as session:

            existing_user_query = await session.execute(
                select(UserOrm).where(
                    (UserOrm.email == data.email) | (UserOrm.phone == data.phone)
                )
            )
            if existing_user_query.scalar_one_or_none():
                raise IntegrityError("User with this email or phone already exists.", params=None, orig=None)

            user_dict = data.model_dump()
            user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
            user_dict["handle"] = await generate_unique_handle(data.full_name)

            new_user = UserOrm(**user_dict)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user

    @classmethod
    async def get_user_by_email(cls, email: str) -> UserOrm | None:
        """Находит пользователя по email."""
        async with new_session() as session:
            query = select(UserOrm).where(UserOrm.email == email)
            result = await session.execute(query)
            return result.scalar_one_or_none()