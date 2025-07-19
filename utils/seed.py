import datetime
import random

from sqlalchemy import select
from db import new_session
from db.events import EventActivityOrm, EventOrm, EventParticipationOrm, ParticipantTypeEnum, ParticipationMemberOrm, \
    ScoreOrm
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
    },
    **{f"player{i}": {
        "handle": f"10{i}",
        "email": f"player{i}@test.com",
        "password": "password",
        "full_name": f"Игрок {i}",
        "avatar_url": f"https://i.pravatar.cc/150?u=player{i}",
        "phone": f"+711122233{i:02d}"} for i in range(20)
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


async def create_leaderboard_data():
    """Создает два мероприятия с участниками и очками для теста лидерборда."""
    print("Проверка и создание данных для лидерборда...")
    async with new_session() as session:
        # 1. Проверяем, создано ли уже событие для теста, и выходим, если да
        res_check = await session.execute(
            select(EventOrm).where(EventOrm.title == "Чемпионат по скоростному программированию"))
        if res_check.scalar_one_or_none():
            print("Данные для лидерборда уже существуют.")
            return

        print("Создание тестовых мероприятий и участников для лидерборда...")
        today = datetime.date.today()

        # 2. Создаем 3 активности, которые будем переиспользовать
        activities_data = [
            {"name": "Отборочный тур", "is_scoreable": True, "max_score": 100},
            {"name": "Полуфинал", "is_scoreable": True, "max_score": 200},
            {"name": "Гранд-финал", "is_scoreable": True, "max_score": 300},
        ]

        # 3. Создаем командное мероприятие
        team_event = EventOrm(
            title="Чемпионат по скоростному программированию",
            date=today,
            is_team=True, max_members=50, max_teams=10,
            activities=[EventActivityOrm(**ad) for ad in activities_data]
        )
        session.add(team_event)

        # 4. Создаем личное мероприятие
        solo_event = EventOrm(
            title="Одиночный турнир по решению задач",
            date=today,
            is_team=False, max_members=10,
            activities=[EventActivityOrm(**ad) for ad in activities_data]
        )
        session.add(solo_event)

        # Получаем ID событий и активностей
        await session.flush()

        # 5. Находим всех наших "игроков"
        res_players = await session.execute(select(UserOrm).where(UserOrm.email.like("player%@test.com")))
        players = res_players.scalars().all()

        # 6. Создаем 10 команд и начисляем им очки
        for i in range(10):
            captain = players[i]
            member = players[i + 10]
            team_participation = EventParticipationOrm(
                event_id=team_event.id, creator_id=captain.id,
                participant_type=ParticipantTypeEnum.team, team_name=f"Команда #{i + 1}"
            )
            team_participation.members.extend([
                ParticipationMemberOrm(user_id=captain.id),
                ParticipationMemberOrm(user_id=member.id)
            ])
            session.add(team_participation)
            await session.flush()  # Получаем ID участия

            # Начисляем очки за каждую активность
            for activity in team_event.activities:
                score = ScoreOrm(
                    participation_id=team_participation.id, activity_id=activity.id,
                    score=random.randint(20, activity.max_score)
                )
                session.add(score)

        # 7. Регистрируем 10 одиночных игроков и начисляем им очки
        for i in range(10):
            player = players[i]
            solo_participation = EventParticipationOrm(
                event_id=solo_event.id, creator_id=player.id,
                participant_type=ParticipantTypeEnum.individual
            )
            solo_participation.members.append(ParticipationMemberOrm(user_id=player.id))
            session.add(solo_participation)
            await session.flush()

            # Начисляем очки за каждую активность
            for activity in solo_event.activities:
                score = ScoreOrm(
                    participation_id=solo_participation.id, activity_id=activity.id,
                    score=random.randint(10, activity.max_score)
                )
                session.add(score)

        await session.commit()
    print("Создание данных для лидерборда завершено.")
