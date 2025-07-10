from typing import Optional

from sqlalchemy import select, update, delete, exists

from db import new_session
from db.events import EventActivityOrm, EventOrm
from events.schemas import SActivityUpdate, SActivityAdd


class ActivityRepository:

    @classmethod
    async def add_one(cls, event_id: int, data: SActivityAdd) -> Optional[int]:
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
    async def get_by_event_id(cls, event_id: int) -> list[EventActivityOrm]:
        async with new_session() as s:
            q = select(EventActivityOrm).where(EventActivityOrm.event_id == event_id)
            return (await s.execute(q)).scalars().all()

    @classmethod
    async def edit_one(cls, id: int, data: SActivityUpdate) -> bool:
        async with new_session() as s:
            d = data.model_dump(exclude_unset=True)
            if not d: return False
            q = update(EventActivityOrm).where(EventActivityOrm.id == id).values(**d)
            res = await s.execute(q)
            await s.commit()
            return bool(res.rowcount)

    @classmethod
    async def delete_one(cls, id: int) -> bool:
        async with new_session() as s:
            q = delete(EventActivityOrm).where(EventActivityOrm.id == id)
            res = await s.execute(q)
            await s.commit()
            return bool(res.rowcount)
