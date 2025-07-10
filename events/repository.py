from typing import List, Optional

from sqlalchemy import func, select, delete, update, exists
from sqlalchemy.orm import selectinload

from db import new_session
from db.events import EventOrm, EventMediaOrm
from helpers.validators import validate_limits
from .schemas import SEventAdd, SEvent, SEventUpdate, SEventMediaAdd, SMediaReorderItem


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
                update_data["max_teams"] = None

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
            res = await session.execute(delete(EventOrm).where(EventOrm.id == event_id))
            await session.commit()
            return bool(res.rowcount)

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
