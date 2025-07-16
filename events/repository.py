import uuid
from typing import List, Optional

from sqlalchemy import func, select, delete, update, exists
from sqlalchemy.orm import selectinload

from db import new_session
from db.events import EventOrm, EventMediaOrm, ParticipationMemberOrm, EventParticipationOrm, ParticipantTypeEnum, \
    EventJudgeOrm, ScoreOrm
from db.users import UserOrm, RoleEnum
from helpers.validators import validate_limits
from events.schemas import SEventAdd, SEvent, SEventUpdate, SEventMediaAdd, SMediaReorderItem, SParticipationCreate, \
    SScoreAdd, SJudgeAdd


class EventRepository:
    @classmethod
    async def get_all(cls) -> List[SEvent]:
        async with new_session() as session:
            res = await session.execute(select(EventOrm).options(selectinload(EventOrm.media)))
            events = res.scalars().all()
            cards = []

            for e in events:
                # preview_url: media_type==image, order==0
                preview_url = None
                for m in e.media:
                    if m.media_type == "image" and m.order == 0:
                        preview_url = m.url
                        break
                cards.append({
                    "id": e.id,
                    "title": e.title,
                    "date": e.date,
                    "state": e.state,
                    "preview_url": preview_url,
                    "is_team": e.is_team,
                })

            return cards

    @classmethod
    async def get_by_id(cls, event_id: int) -> Optional[SEvent]:
        async with new_session() as session:
            query = (
                select(EventOrm)
                .where(EventOrm.id == event_id)
                .options(
                    selectinload(EventOrm.media),
                    selectinload(EventOrm.activities)
                )
            )

            result = await session.execute(query)
            event_orm = result.scalar_one_or_none()

            if not event_orm:
                return None

            return SEvent.model_validate(event_orm, from_attributes=True)

    @classmethod
    async def add_one(cls, data: SEventAdd) -> int:
        async with new_session() as session:
            event = EventOrm(**data.model_dump())
            session.add(event)
            await session.commit()
            await session.refresh(event)
            return event.id

    @classmethod
    async def edit(cls, event_id: int, payload: SEventUpdate) -> bool:
        update_data = payload.model_dump(exclude_unset=True, exclude_none=True)

        if not update_data:
            return False

        async with new_session() as session:
            event = await session.get(EventOrm, event_id)
            if not event:
                return False

            # Null out max_teams if is_team is False
            if event.is_team == True and payload.is_team == False:
                event.max_teams = None

            # Validate max_teams
            max_members = payload.max_members if payload.max_members is not None else event.max_members
            max_teams = payload.max_teams if payload.max_teams is not None else event.max_teams
            is_team = payload.is_team if payload.is_team is not None else event.is_team

            validate_limits(is_team, max_members, max_teams)

            stmt = (
                update(EventOrm)
                .where(EventOrm.id == event_id)
                .values(**update_data)
                .execution_options(synchronize_session="fetch")
            )
            res = await session.execute(stmt)
            await session.commit()
            return bool(res.rowcount)

    @classmethod
    async def delete(cls, event_id: int) -> bool:
        async with new_session() as session:
            event = await session.get(EventOrm, event_id)
            if event is None:
                return False
            await session.delete(event)
            await session.commit()
            return True

    @classmethod
    async def add_media(cls, event_id: int, data: SEventMediaAdd) -> Optional[int]:
        async with new_session() as session:
            event_exists = await session.scalar(select(exists().where(EventOrm.id == event_id)))
            if not event_exists:
                return None

            media = EventMediaOrm(event_id=event_id, **data.model_dump())
            session.add(media)
            await session.commit()
            await session.refresh(media)
            return media.id

    @classmethod
    async def delete_media(cls, event_id: int, media_id: int) -> bool:
        async with new_session() as session:
            stmt = delete(EventMediaOrm).where(
                EventMediaOrm.event_id == event_id,
                EventMediaOrm.id == media_id
            )
            res = await session.execute(stmt)
            await session.commit()
            return bool(res.rowcount)

    @classmethod
    async def reorder_media(cls, event_id: int, items: list[SMediaReorderItem]) -> bool:
        if not items:
            return False

        ids = {i.id for i in items}
        new_map = {i.id: i.order for i in items}

        async with new_session() as s:
            rows = await s.execute(
                select(func.count()).select_from(EventMediaOrm).where(
                    EventMediaOrm.id.in_(ids),
                    EventMediaOrm.event_id == event_id
                )
            )
            if rows.scalar_one() != len(ids):
                raise ValueError("media ids mismatch event")

            for mid, new_ord in new_map.items():
                await s.execute(
                    update(EventMediaOrm)
                    .where(EventMediaOrm.id == mid)
                    .values(order=new_ord)
                )
            await s.commit()
            return True

    @classmethod
    async def add_participation(
            cls, event_id: int, user_id: uuid.UUID, data: SParticipationCreate
    ) -> EventParticipationOrm:
        """Создает новое участие (личное или команду)."""
        async with new_session() as session:
            existing_participation = await session.execute(
                select(ParticipationMemberOrm).join(EventParticipationOrm).where(
                    ParticipationMemberOrm.user_id == user_id,
                    EventParticipationOrm.event_id == event_id
                )
            )
            if existing_participation.scalar_one_or_none():
                raise ValueError("Пользователь уже участвует в этом мероприятии.")

            event = await session.get(EventOrm, event_id)
            if not event:
                raise ValueError("Мероприятие не найдено.")

            current_participations = await cls.get_participations_for_event(event_id)

            if data.participant_type == ParticipantTypeEnum.individual:
                current_individual_members = sum(
                    1 for p in current_participations if p.participant_type == 'individual')
                if current_individual_members >= event.max_members:
                    raise ValueError("Достигнут лимит участников в личном зачете.")

            if data.participant_type == ParticipantTypeEnum.team:
                if not event.is_team or not event.max_teams:
                    raise ValueError("Это мероприятие не является командным.")
                current_teams_count = sum(1 for p in current_participations if p.participant_type == 'team')
                if current_teams_count >= event.max_teams:
                    raise ValueError("Достигнут лимит команд в мероприятии.")

            new_participation = EventParticipationOrm(
                event_id=event_id,
                creator_id=user_id,
                participant_type=data.participant_type,
                team_name=data.team_name if data.participant_type == ParticipantTypeEnum.team else None,
            )
            session.add(new_participation)
            await session.flush()

            creator_as_member = ParticipationMemberOrm(
                participation_id=new_participation.id,
                user_id=user_id
            )
            session.add(creator_as_member)
            await session.commit()

            full_participation = await cls.get_participation_by_id(new_participation.id)
            return full_participation

    @classmethod
    async def get_participations_for_event(cls, event_id: int) -> list[EventParticipationOrm]:
        """Возвращает список всех участий для мероприятия."""
        async with new_session() as session:
            query = (
                select(EventParticipationOrm)
                .where(EventParticipationOrm.event_id == event_id)
                .options(
                    selectinload(EventParticipationOrm.creator),
                    selectinload(EventParticipationOrm.members).selectinload(ParticipationMemberOrm.user)
                )
            )
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_participation_by_id(cls, participation_id: int) -> EventParticipationOrm | None:
        async with new_session() as session:
            query = (
                select(EventParticipationOrm)
                .where(EventParticipationOrm.id == participation_id)
                .options(
                    selectinload(EventParticipationOrm.creator),
                    selectinload(EventParticipationOrm.members).selectinload(ParticipationMemberOrm.user)
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def add_member_to_participation(cls, participation_id: int, user_id: uuid.UUID):
        """Добавляет нового участника в существующее участие (команду)."""
        async with new_session() as session:
            # Получаем участие и связанных с ним членов
            participation = await cls.get_participation_by_id(participation_id)
            if not participation:
                raise ValueError("Команда или участие не найдены.")

            # Проверяем, что это командное участие
            if participation.participant_type != ParticipantTypeEnum.team:
                raise ValueError("Нельзя присоединиться к индивидуальному участию.")

            # Проверяем, есть ли места в команде
            event = await session.get(EventOrm, participation.event_id)
            if len(participation.members) >= event.max_members:
                raise ValueError("Команда уже заполнена.")

            # Проверяем, не участвует ли пользователь уже в этом мероприятии
            existing_member = await session.execute(
                select(ParticipationMemberOrm).join(EventParticipationOrm).where(
                    ParticipationMemberOrm.user_id == user_id,
                    EventParticipationOrm.event_id == participation.event_id
                )
            )
            if existing_member.scalar_one_or_none():
                raise ValueError("Пользователь уже участвует в этом мероприятии.")

            # Добавляем участника
            new_member = ParticipationMemberOrm(participation_id=participation_id, user_id=user_id)
            session.add(new_member)
            await session.commit()

    @classmethod
    async def remove_member_from_participation(cls, participation_id: int, user_id_to_remove: uuid.UUID,
                                               current_user_id: uuid.UUID):
        """Удаляет участника из команды или обрабатывает выход капитана."""
        async with new_session() as session:
            participation = await cls.get_participation_by_id(participation_id)
            if not participation:
                raise ValueError("Команда не найдена.")

            is_self_kick = user_id_to_remove == current_user_id
            is_captain_action = participation.creator_id == current_user_id

            # Если капитан выходит из команды сам
            if is_self_kick and is_captain_action:
                return await cls.captain_leaves_team(participation_id, current_user_id)

            # Если капитан кикает другого
            if is_captain_action and not is_self_kick:
                member_to_delete = await session.get(ParticipationMemberOrm, (participation_id, user_id_to_remove))
                if not member_to_delete: raise ValueError("Участник не найден в этой команде.")
                await session.delete(member_to_delete)
                await session.commit()
                return

            # Если обычный участник выходит сам
            if is_self_kick and not is_captain_action:
                member_to_delete = await session.get(ParticipationMemberOrm, (participation_id, user_id_to_remove))
                if not member_to_delete: raise ValueError("Участник не найден в этой команде.")
                await session.delete(member_to_delete)
                await session.commit()
                return

            raise PermissionError("У вас нет прав для выполнения этого действия.")

    @classmethod
    async def delete_participation(cls, participation_id: int, current_user_id: uuid.UUID):
        """Удаляет участие (команду). Только для создателя."""
        async with new_session() as session:
            participation = await session.get(EventParticipationOrm, participation_id)
            if not participation:
                return

            if participation.creator_id != current_user_id:
                raise PermissionError("Только создатель может удалить команду/участие.")

            await session.delete(participation)
            await session.commit()

    @classmethod
    async def get_participations_for_user(cls, user_id: uuid.UUID) -> list[EventParticipationOrm]:
        """Возвращает список всех участий для конкретного пользователя."""
        async with new_session() as session:
            query = select(EventParticipationOrm).join(ParticipationMemberOrm).where(
                ParticipationMemberOrm.user_id == user_id
            ).options(
                selectinload(EventParticipationOrm.creator),
                selectinload(EventParticipationOrm.members).selectinload(ParticipationMemberOrm.user)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def transfer_captaincy(cls, participation_id: int, new_captain_id: uuid.UUID, current_captain_id: uuid.UUID):
        """Передает права капитана новому участнику."""
        async with new_session() as session:
            participation = await session.get(EventParticipationOrm, participation_id)
            if not participation or participation.creator_id != current_captain_id:
                raise PermissionError("Только текущий капитан может передать права.")

            # Проверяем, что новый капитан является членом команды
            new_captain_member = await session.get(ParticipationMemberOrm, (participation_id, new_captain_id))
            if not new_captain_member:
                raise ValueError("Новый капитан должен быть участником команды.")

            participation.creator_id = new_captain_id
            await session.commit()

    @classmethod
    async def captain_leaves_team(cls, participation_id: int, captain_id: uuid.UUID):
        """Обрабатывает выход капитана из команды."""
        async with new_session() as session:
            participation = await cls.get_participation_by_id(participation_id)
            if not participation or participation.creator_id != captain_id:
                raise PermissionError("Ошибка прав доступа.")

            if len(participation.members) == 1:
                await session.delete(participation)
                await session.commit()
                return

            # --- НОВАЯ, ЕЩЕ БОЛЕЕ НАДЕЖНАЯ ЛОГИКА ---

            # 1. Удаляем капитана из таблицы members
            stmt_delete = delete(ParticipationMemberOrm).where(
                ParticipationMemberOrm.participation_id == participation_id,
                ParticipationMemberOrm.user_id == captain_id
            )
            await session.execute(stmt_delete)

            # 2. Находим ID нового капитана (первый из оставшихся)
            new_captain_member = next((m for m in participation.members if m.user_id != captain_id), None)
            if not new_captain_member:
                # Если по какой-то причине некого назначить, распускаем команду
                stmt_delete_participation = delete(EventParticipationOrm).where(
                    EventParticipationOrm.id == participation_id)
                await session.execute(stmt_delete_participation)
                await session.commit()
                return

            # 3. Обновляем creator_id в таблице participations
            new_captain_id = new_captain_member.user_id
            stmt_update = update(EventParticipationOrm).where(
                EventParticipationOrm.id == participation_id
            ).values(creator_id=new_captain_id)

            await session.execute(stmt_update)

            # 4. Коммитим обе операции (DELETE и UPDATE)
            await session.commit()

    @classmethod
    async def add_judge_to_event(cls, event_id: int, data: SJudgeAdd):
        async with new_session() as session:
            # Проверяем, не является ли пользователь уже участником этого мероприятия
            participation = await session.execute(
                select(ParticipationMemberOrm).join(EventParticipationOrm).where(
                    ParticipationMemberOrm.user_id == data.user_id,
                    EventParticipationOrm.event_id == event_id
                )
            )
            if participation.scalar_one_or_none():
                raise ValueError("Этот пользователь уже является участником и не может быть назначен судьей.")

            new_judge = EventJudgeOrm(event_id=event_id, **data.model_dump())
            session.add(new_judge)
            await session.commit()

    @classmethod
    async def add_score(cls, user_id: uuid.UUID, data: SScoreAdd):
        async with new_session() as session:
            # Получаем ивент, чтобы проверить права
            participation = await session.get(EventParticipationOrm, data.participation_id)
            if not participation:
                raise ValueError("Участие не найдено.")

            event = await session.get(EventOrm, participation.event_id)
            user_role = (await session.get(UserOrm, user_id)).role

            # Проверка прав: Админ или Организатор могут добавлять очки без привязки к активности
            if data.activity_id is None:
                if user_role not in [RoleEnum.admin, RoleEnum.organizer]:
                    raise PermissionError("Только администратор или организатор могут добавлять бонусные очки.")

            # Если activity_id указан, проверяем, является ли пользователь судьей
            else:
                is_judge = await session.get(EventJudgeOrm, (event.id, user_id))
                if not is_judge and user_role not in [RoleEnum.admin, RoleEnum.organizer]:
                    raise PermissionError("Только назначенный судья может выставлять оценки за активности.")

                # Тут можно добавить проверку на max_score, если нужно

            new_score = ScoreOrm(
                judge_id=user_id if data.activity_id is not None else None,
                **data.model_dump()
            )
            session.add(new_score)
            await session.commit()
