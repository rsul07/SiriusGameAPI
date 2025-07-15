import uuid
from typing import List, Optional

from sqlalchemy import func, select, delete, update, exists
from sqlalchemy.orm import selectinload

from db import new_session
from db.events import EventOrm, EventMediaOrm, ParticipationMemberOrm, EventParticipationOrm, ParticipantTypeEnum
from helpers.validators import validate_limits
from events.schemas import SEventAdd, SEvent, SEventUpdate, SEventMediaAdd, SMediaReorderItem, SParticipationCreate


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
            return new_participation

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
        """Удаляет участника из команды."""
        async with new_session() as session:
            participation = await cls.get_participation_by_id(participation_id)
            if not participation:
                raise ValueError("Команда не найдена.")

            is_self_kick = user_id_to_remove == current_user_id
            is_captain = participation.creator_id == current_user_id

            # --- Логика прав ---
            if not is_self_kick and not is_captain:
                raise PermissionError("Только капитан может удалять других участников.")

            # Важное правило: капитан не может покинуть команду, он может ее только распустить
            if is_self_kick and is_captain:
                raise ValueError("Капитан не может покинуть команду. Он может только удалить ее.")

            # Находим и удаляем участника
            member_to_delete = await session.get(ParticipationMemberOrm, (participation_id, user_id_to_remove))
            if not member_to_delete:
                raise ValueError("Участник не найден в этой команде.")

            await session.delete(member_to_delete)
            await session.commit()

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
