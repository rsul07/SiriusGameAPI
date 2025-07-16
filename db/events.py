import datetime
import uuid
from enum import Enum
from typing import List

from sqlalchemy import ForeignKey, Enum as SQLEnum, Index, String, Boolean, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Model
from db.users import UserOrm


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
        order_by="EventMediaOrm.order",
    )

    activities: Mapped[List["EventActivityOrm"]] = relationship(
        back_populates="event",
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
    name: Mapped[str | None] = mapped_column()  # not required for images
    order: Mapped[int] = mapped_column(default=0, nullable=False)  # will be used for images

    __table_args__ = (Index("idx_event_media", "event_id", "order"),)  # speed up slider sorting


class EventActivityOrm(Model):
    __tablename__ = "event_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50))

    latitude: Mapped[float | None] = mapped_column(Numeric(10, 6))
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 6))

    is_scoreable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_versus: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_score: Mapped[int | None] = mapped_column()
    start_dt: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))
    end_dt: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True))

    event: Mapped["EventOrm"] = relationship(back_populates="activities")


class ParticipantTypeEnum(str, Enum):
    individual = "individual"
    team = "team"


class EventParticipationOrm(Model):
    __tablename__ = "event_participations"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    participant_type: Mapped[ParticipantTypeEnum] = mapped_column(
        SQLEnum(ParticipantTypeEnum, name="participant_type_enum"), nullable=False
    )
    team_name: Mapped[str | None] = mapped_column(String(80))
    registered_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(), nullable=False)

    creator: Mapped["UserOrm"] = relationship(foreign_keys=[creator_id])
    members: Mapped[list["ParticipationMemberOrm"]] = relationship(
        back_populates="participation",
        cascade="all, delete-orphan"
    )


class ParticipationMemberOrm(Model):
    __tablename__ = "participation_members"

    participation_id: Mapped[int] = mapped_column(
        ForeignKey("event_participations.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    user: Mapped["UserOrm"] = relationship()
    participation: Mapped["EventParticipationOrm"] = relationship(back_populates="members")
