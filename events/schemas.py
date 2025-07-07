import datetime as dt
from typing import Literal, List

from pydantic import BaseModel, Field, field_validator, computed_field, model_validator
from db.events import MediaEnum


# Media
class _EventMedia(BaseModel):
    url: str
    media_type: MediaEnum = MediaEnum.image
    name: str | None = None
    order: int = 0  # used by image slider


class SEventMediaAdd(_EventMedia):
    pass


class SEventMedia(_EventMedia):
    id: int
    event_id: int

    model_config = {"from_attributes": True}


# Events
class EventExtrasMixin(BaseModel):
    description: str | None = None
    start_time: dt.time | None = None
    end_time: dt.time | None = None
    max_members: int | None = None
    max_teams: int | None = None

    @model_validator(mode="after")
    def validate_limits(self):
        if self.max_members is not None and self.max_teams is not None:
            raise ValueError("Cannot set both max_members and max_teams")

        if self.is_team is True and self.max_teams is None:
            raise ValueError("max_teams required when is_team=True")
        if self.is_team is False and self.max_members is None:
            raise ValueError("max_members required when is_team=False")

        return self


class _EventBase(EventExtrasMixin):
    title: str = Field(..., max_length=120)
    date: dt.date
    is_team: bool

    @field_validator("title", mode="before")
    def strip_title(cls, v: str) -> str:
        return v.strip()


# CRUD event schemas
class SEventAdd(_EventBase):
    pass


class SEventUpdate(EventExtrasMixin):
    title: str | None = Field(None, max_length=120)
    date: dt.date | None = None
    is_team: bool | None = None


class SEventId(BaseModel):
    ok: bool = True
    event_id: int


class SEventActivity(BaseModel):
    id: int
    name: str
    is_required: bool
    icon: str | None = None
    color: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    model_config = {"from_attributes": True}


class SEventActivityAdd(BaseModel):
    name: str = Field(..., max_length=100)
    is_required: bool = True
    icon: str | None = Field(None, max_length=50)
    color: str | None = Field(None, max_length=50)
    latitude: float | None = None
    longitude: float | None = None


# Event
class SEvent(_EventBase):
    id: int
    media: list[SEventMedia]
    activities: List[SEventActivity]

    model_config = {"from_attributes": True}

    @computed_field(return_type=Literal["future", "current", "past"])
    def state(self) -> str:
        now = dt.datetime.now(dt.timezone.utc)  # aware-datetime

        start_dt = (
            dt.datetime.combine(self.date, self.start_time, tzinfo=dt.timezone.utc) if self.start_time
            else dt.datetime.combine(self.date, dt.time.min, tzinfo=dt.timezone.utc)
        )

        end_dt = (
            dt.datetime.combine(self.date, self.end_time, tzinfo=dt.timezone.utc) if self.end_time
            else dt.datetime.combine(self.date, dt.time.max, tzinfo=dt.timezone.utc)
        )

        if start_dt <= now <= end_dt:
            return "current"
        if now < start_dt:
            return "future"
        return "past"
