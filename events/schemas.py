import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field, field_validator, computed_field, model_validator
from db.events import MediaEnum

# Media
class _EventMedia(BaseModel):
    url: str
    media_type: MediaEnum = MediaEnum.image
    name: str | None = None
    order: int = 0                     # used by image slider

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
    max_teams: int | None = None

class _EventBase(EventExtrasMixin):
    title: str = Field(..., max_length=120)
    date: dt.date
    is_team: bool
    max_members: int

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

# Event card schema for listing
class SEventCard(BaseModel):
    id: int
    title: str
    date: dt.date
    state: Literal["future", "current", "past"]
    preview_url: str | None = None
    is_team: bool

# Event
class SEvent(_EventBase):
    id: int
    media: list[SEventMedia]

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