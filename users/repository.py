import random
import string
import uuid

from sqlalchemy import select, or_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db import new_session
from db.users import UserOrm
from users.schemas import SUserRegister, SUserUpdate
from auth.security import get_password_hash, verify_password
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
    async def get_user_by_login_identifier(cls, login_identifier: str) -> UserOrm | None:
        """
        Находит пользователя по email или номеру телефона.
        """
        async with new_session() as session:
            query = select(UserOrm).where(
                or_(
                    UserOrm.email == login_identifier,
                    UserOrm.phone == login_identifier
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def get_user_by_id(cls, user_id: uuid.UUID) -> UserOrm | None:
        """Находит пользователя по его UUID."""
        async with new_session() as session:
            query = select(UserOrm).where(UserOrm.id == user_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def update_user(cls, user_id: uuid.UUID, data: SUserUpdate) -> UserOrm | None:
        """Обновляет данные пользователя."""
        async with new_session() as session:
            update_data = data.model_dump(exclude_unset=True)

            if not update_data:
                return await cls.get_user_by_id(user_id)

            stmt = (
                update(UserOrm)
                .where(UserOrm.id == user_id)
                .values(**update_data)
                .returning(UserOrm)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.scalar_one_or_none()

    @classmethod
    async def update_password(cls, user_id: uuid.UUID, old_password: str, new_password: str) -> bool:
        """Проверяет старый пароль и обновляет на новый."""
        async with new_session() as session:
            user = await session.get(UserOrm, user_id)
            if not user or not verify_password(old_password, user.hashed_password):
                return False
            new_hashed_password = get_password_hash(new_password)
            stmt = (
                update(UserOrm)
                .where(UserOrm.id == user_id)
                .values(hashed_password=new_hashed_password)
            )
            await session.execute(stmt)
            await session.commit()
            return True

    @classmethod
    async def get_user_by_handle(cls, handle: str) -> UserOrm | None:
        """Находит пользователя по его handle."""
        async with new_session() as session:
            query = select(UserOrm).where(UserOrm.handle == handle)
            result = await session.execute(query)
            return result.scalar_one_or_none()
