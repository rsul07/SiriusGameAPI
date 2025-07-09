import datetime
from typing import List, Optional

from sqlalchemy import select, delete, update, exists
from sqlalchemy.orm import selectinload

from db import new_session
from db.events import EventOrm, EventMediaOrm
from events.schemas import SEventAdd, SEvent, SEventUpdate, SEventMediaAdd

class EventRepository:
    @classmethod
    async def get_all(cls) -> List[SEvent]:
        async with new_session() as session:
            res = await session.execute(select(EventOrm).options(selectinload(EventOrm.media)))
            events = res.scalars().all()
            cards = []
            now = datetime.datetime.now(datetime.timezone.utc)
            for e in events:
                # Compute state
                start_dt = datetime.datetime.combine(e.date, e.start_time or datetime.time.min, tzinfo=datetime.timezone.utc)
                end_dt = datetime.datetime.combine(e.date, e.end_time or datetime.time.max, tzinfo=datetime.timezone.utc)
                if start_dt <= now <= end_dt:
                    state = "current"
                elif now < start_dt:
                    state = "future"
                else:
                    state = "past"
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
                    "state": state,
                    "preview_url": preview_url,
                    "is_team": e.is_team,
                })
            if not cards:
                from fastapi import HTTPException
                raise HTTPException(404, "No events found")
            return cards

    @classmethod
    async def get_by_id(cls, event_id: int) -> SEvent | None:
        async with new_session() as session:
            res = await session.execute(
                select(EventOrm).options(selectinload(EventOrm.media)).where(EventOrm.id == event_id)
            )
            event = res.scalar_one_or_none()
            if not event:
                return None
            return SEvent.model_validate(event, from_attributes=True)
        
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