from sqlalchemy import select, update, delete
from db import new_session
from db.events import EventActivityOrm
from events.schemas import SActivityAdd, SActivityUpdate


class ActivityRepository:
    @classmethod
    async def get_by_event_id(cls, event_id: int) -> list[EventActivityOrm]:
        async with new_session() as s:
            q = select(EventActivityOrm).where(EventActivityOrm.event_id == event_id)
            return (await s.execute(q)).scalars().all()

    @classmethod
    async def add_one(cls, event_id: int, data: SActivityAdd) -> int:
        async with new_session() as s:
            activity = EventActivityOrm(event_id=event_id, **data.model_dump())
            s.add(activity)
            await s.commit()
            return activity.id

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
