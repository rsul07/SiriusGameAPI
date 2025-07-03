import datetime
from enum import Enum as PyEnum
from sqlalchemy import Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Model

class TypeEnum(str, PyEnum):
    individual = "individual"
    team = "team"

class EventOrm(Model):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column()
    date: Mapped[datetime.datetime] = mapped_column()
    type: Mapped[TypeEnum] = mapped_column(SQLEnum(TypeEnum))
    rules: Mapped[dict | None] = mapped_column(JSON)

    images: Mapped[list["EventImageOrm"]] = relationship(
        backref="event",
        cascade="all, delete-orphan",
    )

class EventImageOrm(Model):
    __tablename__ = "event_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    url: Mapped[str]
