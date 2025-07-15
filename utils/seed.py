import datetime
from sqlalchemy import select
from db import new_session
from db.events import EventActivityOrm, EventOrm
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


INITIAL_EVENTS = [
    {
        "title": "Летний марафон кода",
        "description": "Ежегодный марафон для лучших программистов. 24 часа непрерывного кодинга, пицца и энергетики!",
        "date": datetime.date.today() + datetime.timedelta(days=30),  # Будущее
        "start_time": datetime.time(12, 0),
        "end_time": datetime.time(12, 0),  # На следующий день, но дата одна
        "is_team": False,
        "max_members": 100,
        "max_teams": None,
        "activities": [
            {"name": "Регистрация и получение мерча", "icon": "👕", "start_dt": datetime.datetime(2025, 8, 15, 12, 0),
             "end_dt": datetime.datetime(2025, 8, 15, 13, 0)},
            {"name": "Начало контеста", "icon": "💻", "start_dt": datetime.datetime(2025, 8, 15, 13, 0),
             "end_dt": datetime.datetime(2025, 8, 16, 13, 0)},
            {"name": "Награждение победителей", "icon": "🏆", "start_dt": datetime.datetime(2025, 8, 16, 14, 0),
             "end_dt": datetime.datetime(2025, 8, 16, 15, 0)},
        ]
    },
    {
        "title": "Чемпионат по робототехнике",
        "description": "Соберите своего робота и сразитесь на арене. Главный приз - стажировка в ведущей IT-компании.",
        "date": datetime.date.today(),  # Текущее
        "start_time": datetime.time(9, 0),
        "end_time": datetime.time(18, 0),
        "is_team": True,
        "max_members": 20,
        "max_teams": 5,
        "activities": [
            {"name": "Сборка и настройка роботов", "icon": "🛠️", "is_scoreable": True, "max_score": 50},
            {"name": "Квалификационные заезды", "icon": "⏱️", "is_scoreable": True, "is_versus": True,
             "max_score": 100},
            {"name": "Финальная битва роботов", "icon": "🤖", "is_scoreable": True, "is_versus": True, "max_score": 200},
        ]
    },
    {
        "title": "Хакатон 'Умный Город'",
        "description": "Разработайте решение для улучшения городской среды за 48 часов. Лучшие проекты будут представлены администрации города.",
        "date": datetime.date.today() - datetime.timedelta(days=60),  # Прошедшее
        "start_time": datetime.time(18, 0),
        "end_time": datetime.time(18, 0),
        "is_team": True,
        "max_members": 30,
        "max_teams": 6,
        "activities": []
    }
]


async def create_initial_events():
    """Создает начальные мероприятия с активностями, если их еще нет."""
    print("Проверка и создание начальных мероприятий...")
    async with new_session() as session:
        for event_data in INITIAL_EVENTS:
            event_exists = await session.execute(
                select(EventOrm).where(EventOrm.title == event_data["title"])
            )
            if not event_exists.scalar_one_or_none():
                print(f"Создание мероприятия: {event_data['title']}")
                activities_data = event_data.pop("activities", [])

                new_event = EventOrm(**event_data)

                # Создаем и привязываем активности к событию
                new_event.activities = [
                    EventActivityOrm(**activity) for activity in activities_data
                ]

                session.add(new_event)
        await session.commit()
    print("Проверка мероприятий завершена.")
