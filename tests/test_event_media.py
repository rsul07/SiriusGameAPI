import datetime
import pytest
import pytest_asyncio
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from db.events import EventOrm, EventMediaOrm, MediaEnum
from db import Model  # DeclarativeBase


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    async with async_session() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_media_cascade_delete_bulk_delete(session: AsyncSession):
    event = EventOrm(
        title="Test event",
        date=datetime.date.today(),
        is_team=False, 
        max_members=10
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)

    img = EventMediaOrm(
        event_id=event.id,
        url="http://x.png",
        media_type=MediaEnum.image,
        order=0
    )
    session.add(img)
    await session.commit()

    before = await session.scalar(select(func.count()).select_from(EventMediaOrm))
    assert before == 1

    await session.delete(event)
    await session.commit()

    after = await session.scalar(select(func.count()).select_from(EventMediaOrm))
    assert after == 0

@pytest.mark.asyncio
async def test_media_cascade_delete_not_bulk(session: AsyncSession):
    event = EventOrm(
        title="Test event",
        date=datetime.date.today(),
        is_team=False, 
        max_members=10
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)

    img = EventMediaOrm(
        event_id=event.id,
        url="http://x.png",
        media_type=MediaEnum.image,
        order=0
    )
    session.add(img)
    await session.commit()

    before = await session.scalar(select(func.count()).select_from(EventMediaOrm))
    assert before == 1

    await session.execute(delete(EventOrm).where(EventOrm.id == event.id))
    await session.commit()

    after = await session.scalar(select(func.count()).select_from(EventMediaOrm))
    assert after == 0
