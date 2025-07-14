import datetime
from sqlalchemy import select
from db import new_session
from db.users import UserOrm, RoleEnum
from auth.security import get_password_hash

INITIAL_USERS = {
    "admin": {
        "handle": "1",
        "email": "admin@sirius.com",
        "password": "123456789",
        "full_name": "Главный Администратор",
        "phone": "+70000000001",
        "role": RoleEnum.admin,
    },
    "organizer": {
        "handle": "2",
        "email": "organizer@sirius.com",
        "password": "123456789",
        "full_name": "Главный Организатор",
        "phone": "+70000000002",
        "role": RoleEnum.organizer,
    }
}


async def create_initial_users():
    """Создает начальных пользователей, если их еще нет в БД."""
    print("Проверка и создание начальных пользователей...")
    async with new_session() as session:
        for key, user_data in INITIAL_USERS.items():
            user_exists = await session.execute(
                select(UserOrm).where(UserOrm.handle == user_data["handle"])
            )
            if not user_exists.scalar_one_or_none():
                print(f"Создание пользователя: {key}")
                password = user_data.pop("password")
                user_data["hashed_password"] = get_password_hash(password)

                user_data.setdefault("birthday", datetime.date.fromisoformat("2000-01-01"))
                user_data.setdefault("gender", "male")

                new_user = UserOrm(**user_data)
                session.add(new_user)
        await session.commit()
    print("Проверка завершена.")
