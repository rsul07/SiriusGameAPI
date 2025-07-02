from typing import List, Optional

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db import new_session
from db.events import EventOrm
from events.schemas import SEventAdd, SEvent, SEventUpdate

class EventRepository:
    @classmethod
    async def get_all(cls) -> List[SEvent]:
        async with new_session() as session:
            res = await session.execute(select(EventOrm))
            events = res.scalars().all()
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