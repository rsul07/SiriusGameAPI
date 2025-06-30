import datetime
from sqlalchemy import func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey
from typing import Optional

engine = create_async_engine('sqlite+aiosqlite:///database.db')
new_session = async_sessionmaker(engine, expire_on_commit=False)


class Model(DeclarativeBase):
    pass


class EventOrm(Model):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column()
    latidude: Mapped[float] = mapped_column()
    longitude: Mapped[float] = mapped_column()
    location: Mapped[str] = mapped_column()


class TeamOrm(Model):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    score: Mapped[int] = mapped_column(default=0)


class TeamEventOrm(Model):
    __tablename__ = "teams_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    order: Mapped[int]
    score: Mapped[int]
    state: Mapped[str]


class DeviceEntity(Model):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column()
    systemName: Mapped[Optional[str]] = mapped_column()
    systemVersion: Mapped[Optional[str]] = mapped_column()
    model: Mapped[Optional[str]] = mapped_column()
    localizedModel: Mapped[Optional[str]] = mapped_column()
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now()
    )

    def to_model(self) -> "pushes.schemas.Device":
        from pushes.schemas import Device
        return Device(
            id=self.id,
            token=self.token,
            name=self.name,
            systemName=self.systemName,
            systemVersion=self.systemVersion,
            model=self.model,
            localizedModel=self.localizedModel,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_model(cls, model: "pushes.schemas.Device") -> "DeviceEntity":
        from pushes.schemas import Device
        if not isinstance(model, Device):
            raise TypeError("Input must be a pushes.schemas.Device instance")

        return cls(
            token=model.token,
            name=model.name,
            systemName=model.systemName,
            systemVersion=model.systemVersion,
            model=model.model,
            localizedModel=model.localizedModel,
        )


class NotificationHistoryOrm(Model):
    __tablename__ = "notification_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"),
                                           index=True)
    title: Mapped[str] = mapped_column()
    body: Mapped[str] = mapped_column()
    sent_at: Mapped[datetime.datetime] = mapped_column(default=func.now())
    apns_status: Mapped[str] = mapped_column()
    destination: Mapped[Optional[str]] = mapped_column()
    sound: Mapped[Optional[str]] = mapped_column()

    def to_model(self) -> "NotificationHistory":
        from pushes.schemas import NotificationHistory
        return NotificationHistory(
            id=self.id,
            device_id=self.device_id,
            title=self.title,
            body=self.body,
            sent_at=self.sent_at,
            apns_status=self.apns_status,
            destination=self.destination,
            sound=self.sound,
        )


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)


async def delete_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)
