import datetime
from enum import Enum

from sqlalchemy import ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Model

class EventOrm(Model):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column()
    date: Mapped[datetime.date] = mapped_column(nullable=False)
    start_time: Mapped[datetime.time | None] = mapped_column()
    end_time: Mapped[datetime.time | None] = mapped_column()
    is_team: Mapped[bool] = mapped_column(nullable=False)
    max_members: Mapped[int] = mapped_column(nullable=False)
    max_teams: Mapped[int | None] = mapped_column()

    @property
    def state(self) -> str:
        now = datetime.datetime.now(datetime.timezone.utc)
        start_dt = (
            datetime.datetime.combine(self.date, self.start_time or datetime.time.min,
            tzinfo=datetime.timezone.utc)
        )
        end_dt = (
            datetime.datetime.combine(self.date, self.end_time or datetime.time.max,
            tzinfo=datetime.timezone.utc)
        )
        if start_dt <= now <= end_dt:
            return "current"
        elif now < start_dt:
            return "future"
        return "past"
    
    media: Mapped[list["EventMediaOrm"]] = relationship(
        backref="event",
        cascade="all, delete-orphan",
    )

class MediaEnum(str, Enum):
    image = "image"
    document = "document"

class EventMediaOrm(Model):
    __tablename__ = "event_media"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE")
    )
    media_type: Mapped[MediaEnum] = mapped_column(
        SQLEnum(MediaEnum, name="media_enum"), nullable=False
    )
    url: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str | None] = mapped_column()                          # not required for images 
    order: Mapped[int] = mapped_column(default=0, nullable = False)     # will be used for images

    __table_args__ = (Index("idx_event_media", "event_id", "order"), )  # speed up slider sorting