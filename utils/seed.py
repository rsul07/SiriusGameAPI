import datetime
import random

from sqlalchemy import select
from db import new_session
from db.events import EventActivityOrm, EventOrm, EventParticipationOrm, ParticipantTypeEnum, ParticipationMemberOrm, \
    ScoreOrm, EventJudgeOrm, EventMediaOrm, MediaEnum
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


async def create_demo_events():
    """Создает 6 детализированных мероприятий для демонстрации."""
    print("Проверка и создание демо-мероприятий...")
    async with new_session() as session:
        res_check = await session.execute(select(EventOrm).where(EventOrm.title == "Sirius Summer Volleyball Cup"))
        if res_check.scalar_one_or_none():
            print("Демо-мероприятия уже существуют.")
            return

        print("Создание демо-мероприятий, команд и очков...")
        today = datetime.date(2025, 7, 22)
        res_users = await session.execute(select(UserOrm))
        users = res_users.scalars().all()
        admin, organizer = users[0], users[1]
        players = users[2:]

        # --- ДЕТАЛИЗИРОВАННЫЕ ДАННЫЕ ДЛЯ МЕРОПРИЯТИЙ ---
        DEMO_EVENTS_DATA = [
            # --- ТЕКУЩИЕ ---
            {
                "data": {
                    "title": "Турнир по баскетболу 3x3", "date": today, "is_team": True, "max_teams": 8, "max_members": 40,
                    "start_time": datetime.time(9, 0), "end_time": datetime.time(18, 0),
                    "description": "Приготовьтесь к жаркому асфальту! Ежегодный турнир по стритболу среди лучших команд Сириуса. Динамичные матчи, музыка и отличная атмосфера гарантированы. Покажите свое мастерство владения мячом и командную игру!"
                },
                "media": [{"url": "https://images.unsplash.com/photo-1546519638-68e109498ffc?q=80&w=2070", "name": "Баскетбольная площадка", "media_type": MediaEnum.image}],
                "activities": [
                    {"name": "Церемония открытия", "is_scoreable": False, "icon": "🎉", "latitude": 43.4070, "longitude": 39.9590, "start_dt": datetime.datetime(2025, 7, 21, 9, 0), "end_dt": datetime.datetime(2025, 7, 21, 9, 30)},
                    {"name": "Групповой этап", "is_scoreable": True, "max_score": 100, "icon": "🏀", "latitude": 43.4075, "longitude": 39.9594},
                    {"name": "Плей-офф", "is_scoreable": True, "max_score": 200, "icon": "🏆", "latitude": 43.4080, "longitude": 39.9598},
                ],
                "judges": [organizer],
                "participations": [
                    {"team_name": "Комета", "captain": players[0], "members": [players[1]], "avatar": "https://api.dicebear.com/8.x/shapes/svg?seed=comet"},
                    {"team_name": "Вымпел", "captain": players[2], "members": [players[3]], "avatar": "https://api.dicebear.com/8.x/shapes/svg?seed=vimpel"},
                    {"team_name": "Звезда", "captain": players[4], "members": [players[5]], "avatar": "https://api.dicebear.com/8.x/shapes/svg?seed=star"},
                    {"team_name": "Кристалл", "captain": players[6], "members": [players[7]], "avatar": "https://api.dicebear.com/8.x/shapes/svg?seed=crystal"},
                ]
            },
            {
                "data": {
                    "title": "Открытый турнир по шахматам", "date": today, "is_team": False, "max_members": 10,
                    "start_time": datetime.time(10, 0), "end_time": datetime.time(16, 0),
                    "description": "Интеллектуальная битва для стратегов и тактиков. В этом турнире важны не только знание дебютов, но и выдержка, концентрация и умение мыслить на несколько ходов вперед. Приглашаются все желающие, независимо от рейтинга."
                },
                "media": [{"url": "https://images.unsplash.com/photo-1529699211952-734e80c4d42b?q=80&w=2071", "name": "Шахматная партия", "media_type": MediaEnum.image}],
                "activities": [
                    {"name": "Регистрация участников", "is_scoreable": False, "icon": "📝", "latitude": 43.4090, "longitude": 39.9600, "start_dt": datetime.datetime(2025, 7, 21, 10, 0), "end_dt": datetime.datetime(2025, 7, 21, 11, 0)},
                    {"name": "Блиц-турнир", "is_scoreable": True, "max_score": 50, "icon": "⚡️", "latitude": 43.4095, "longitude": 39.9605},
                    {"name": "Классическая партия", "is_scoreable": True, "max_score": 100, "icon": "♟️", "latitude": 43.4095, "longitude": 39.9605},
                ],
                "judges": [admin],
                "participations": [{"player": p} for p in players[10:18]]
            },
            # --- БУДУЩИЕ ---
            {
                "data": {
                    "title": "Большой теннисный турнир", "date": today + datetime.timedelta(days=14), "is_team": True, "max_teams": 10, "max_members": 40,
                    "description": "Турнир для любителей и профессионалов большого тенниса. Соревнования пройдут на открытых кортах с профессиональным покрытием. Приглашаем команды для участия в парном разряде. Отличная возможность проверить свои силы перед осенним сезоном."
                },
                "media": [{"url": "https://static.ernur.kz/article/5e2e6914850e9.jpg", "name": "Теннисный корт", "media_type": MediaEnum.image}],
                "activities": [
                    {"name": "Регистрация и жеребьевка", "is_scoreable": False, "start_dt": datetime.datetime(2025, 8, 4, 9, 0), "end_dt": datetime.datetime(2025, 8, 4, 10, 0)},
                    {"name": "Парный разряд", "is_scoreable": False, "start_dt": datetime.datetime(2025, 8, 4, 10, 0), "end_dt": datetime.datetime(2025, 8, 4, 14, 0)},
                    {"name": "Одиночный разряд", "is_scoreable": False, "start_dt": datetime.datetime(2025, 8, 4, 14, 0), "end_dt": datetime.datetime(2025, 8, 4, 18, 0)}
                ],
                "participations": [
                    {"team_name": "Подача навылет", "captain": players[8], "members": [players[9]], "avatar": "https://api.dicebear.com/8.x/shapes/svg?seed=ace"},
                ]
            },
            {
                "data": {
                    "title": "Летний легкоатлетический забег", "date": today + datetime.timedelta(days=30), "is_team": False, "max_members": 200,
                    "description": "Традиционный ежегодный забег по Олимпийскому парку. Дистанция 5 километров доступна для всех уровней подготовки. Приходите с семьей и друзьями, чтобы насладиться спортивным праздником и живописными видами."
                },
                "media": [{"url": "https://avatars.mds.yandex.net/i?id=2757793f7648f3b10529faf07980cec5_l-5258779-images-thumbs&n=13", "name": "Бегуны на старте", "media_type": MediaEnum.image}],
                "activities": [
                    {"name": "Выдача стартовых пакетов", "is_scoreable": False, "start_dt": datetime.datetime(2025, 8, 20, 8, 0), "end_dt": datetime.datetime(2025, 8, 20, 9, 30)},
                    {"name": "Старт забега на 5 км", "is_scoreable": False, "start_dt": datetime.datetime(2025, 8, 20, 10, 0), "end_dt": datetime.datetime(2025, 8, 20, 11, 30)},
                    {"name": "Награждение победителей", "is_scoreable": False, "start_dt": datetime.datetime(2025, 8, 20, 12, 0), "end_dt": datetime.datetime(2025, 8, 20, 12, 30)}
                ],
                "participations": []
            },
            # --- ПРОШЕДШИЕ ---
            {
                "data": {
                    "title": "Sirius Summer Volleyball Cup", "date": today - datetime.timedelta(days=20), "is_team": True, "max_teams": 6, "max_members": 30,
                    "description": "Ежегодный кубок по пляжному волейболу. Солнце, песок и напряженные матчи. Команды соревновались за звание чемпионов летнего сезона 2025 года."
                },
                "media": [{"url": "https://avatars.mds.yandex.net/i?id=779be1c7ea939864f4641ed917c827c7_l-10385090-images-thumbs&n=13", "name": "Пляжный волейбол", "media_type": MediaEnum.image}],
                "activities": [{"name": "Первый сет", "is_scoreable": True, "max_score": 25}, {"name": "Второй сет", "is_scoreable": True, "max_score": 25}],
                "participations": [
                    {"team_name": "SunStrikers", "captain": players[10], "members": [players[11]], "avatar": "https://api.dicebear.com/8.x/shapes/svg?seed=sun"},
                    {"team_name": "Net Ninjas", "captain": players[12], "members": [players[13]], "avatar": "https://api.dicebear.com/8.x/shapes/svg?seed=ninja"},
                ]
            },
            {
                "data": {
                    "title": "Состязания по настольному теннису", "date": today - datetime.timedelta(days=45), "is_team": False, "max_members": 15,
                    "description": "Открытые личные состязания по настольному теннису. Турнир проходил по олимпийской системе на выбывание. Участники продемонстрировали высокий уровень мастерства и волю к победе."
                },
                "media": [{"url": "https://avatars.mds.yandex.net/i?id=87dd7fd9ff85ec9d9b95b2743780a8d6_l-9069268-images-thumbs&n=13", "name": "Игра в пинг-понг", "media_type": MediaEnum.image}],
                "activities": [{"name": "Круговой этап", "is_scoreable": True, "max_score": 100}, {"name": "Финал", "is_scoreable": True, "max_score": 150}],
                "participations": [{"player": p} for p in players[0:8]]
            },
        ]

        # --- ИСПРАВЛЕННЫЙ ЦИКЛ СОЗДАНИЯ ---
        for event_info in DEMO_EVENTS_DATA:
            event_data = event_info["data"]
            print(f"Создание демо-мероприятия: {event_data['title']}")

            new_event = EventOrm(**event_data)
            # Теперь данные для активностей полные, is_scoreable больше не хардкодим
            new_event.activities = [EventActivityOrm(**act) for act in event_info.get("activities", [])]
            new_event.media = [EventMediaOrm(**med) for med in event_info.get("media", [])]
            new_event.judges = [EventJudgeOrm(user_id=j.id) for j in event_info.get("judges", [])]
            session.add(new_event)
            await session.flush()

            # Создаем участия и начисляем очки
            for part_data in event_info.get("participations", []):
                if "team_name" in part_data:  # Командное участие
                    p = EventParticipationOrm(
                        event_id=new_event.id, creator_id=part_data["captain"].id,
                        participant_type=ParticipantTypeEnum.team, team_name=part_data["team_name"],
                        team_avatar_url=part_data.get("avatar")
                    )
                    p.members.append(ParticipationMemberOrm(user_id=part_data["captain"].id))
                    for member in part_data["members"]:
                        p.members.append(ParticipationMemberOrm(user_id=member.id))
                else:  # Личное участие
                    player = part_data["player"]
                    p = EventParticipationOrm(
                        event_id=new_event.id, creator_id=player.id,
                        participant_type=ParticipantTypeEnum.individual
                    )
                    p.members.append(ParticipationMemberOrm(user_id=player.id))

                session.add(p)
                await session.flush()

                # Начисляем очки для текущих и прошедших
                if new_event.date <= today:
                    # Перебираем только ОЦЕНИВАЕМЫЕ активности
                    for activity in [act for act in new_event.activities if act.is_scoreable]:
                        score = ScoreOrm(
                            participation_id=p.id, activity_id=activity.id,
                            score=random.randint(int(activity.max_score * 0.4), activity.max_score)
                        )
                        session.add(score)

        await session.commit()
    print("Создание демо-данных завершено.")
