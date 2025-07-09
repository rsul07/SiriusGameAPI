import datetime as dt
from typing import Literal, List

from pydantic import BaseModel, Field, field_validator, computed_field, model_validator
from db.events import MediaEnum
from helpers.validators import validate_limits


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


class SMediaReorderItem(BaseModel):
    id: int
    order: int = Field(..., ge=0)  # order must be non-negative


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
    @model_validator(mode="after")
    def validate_limits_add(self):
        validate_limits(self.is_team, self.max_members, self.max_teams)
        return self


class SEventUpdate(EventExtrasMixin):
    title: str | None = Field(None, max_length=120)
    date: dt.date | None = None
    is_team: bool | None = None
    max_members: int | None = None


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
    state: Literal["future", "current", "past"]
    activities: List[SEventActivity]

    model_config = {"from_attributes": True}
