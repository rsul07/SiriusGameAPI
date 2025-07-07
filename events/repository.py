from typing import List, Optional

from sqlalchemy import select, delete, update, exists
from sqlalchemy.orm import selectinload

from db import new_session
from db.events import EventOrm, EventMediaOrm, EventActivityOrm
from events.schemas import SEventAdd, SEvent, SEventUpdate, SEventMediaAdd, SEventActivityAdd


class EventRepository:
    @classmethod
    async def get_all(cls) -> List[SEvent]:
        async with new_session() as session:
            query = (
                select(EventOrm)
                .options(
                    selectinload(EventOrm.media),
                    selectinload(EventOrm.activities)
                )
            )
            res = await session.execute(query)
            events = res.scalars().unique().all()
            return [SEvent.model_validate(e, from_attributes=True) for e in events]

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

        # prevent setting both max_members and max_teams
        if "is_team" in update_data:
            if update_data["is_team"]:
                update_data["max_members"] = None
            else:
                update_data["max_teams"] = None

        if not update_data:
            return False

        async with new_session() as session:
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
    async def add_activity(cls, event_id: int, data: SEventActivityAdd) -> Optional[int]:
        async with new_session() as session:
            event_exists = await session.scalar(select(exists().where(EventOrm.id == event_id)))
            if not event_exists:
                return None

            activity = EventActivityOrm(event_id=event_id, **data.model_dump())
            session.add(activity)
            await session.commit()
            await session.refresh(activity)
            return activity.id

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
    async def delete_activity(cls, event_id: int, activity_id: int) -> bool:
        async with new_session() as session:
            stmt = delete(EventActivityOrm).where(
                EventMediaOrm.event_id == event_id,
                EventMediaOrm.id == activity_id
            )
            res = await session.execute(stmt)
            await session.commit()
            return bool(res.rowcount)
