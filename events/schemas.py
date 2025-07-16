import datetime as dt
from typing import Literal, List

from pydantic import BaseModel, Field, field_validator, model_validator

from db.events import MediaEnum, ParticipantTypeEnum
from helpers.validators import validate_limits, validate_activity
from users.schemas import SUserPublic


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
    max_members: int = Field(..., gt=0)

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


class SActivityBase(BaseModel):
    name: str = Field(max_length=150)
    icon: str | None = Field(None, max_length=50)
    latitude: float | None = None
    longitude: float | None = None
    is_scoreable: bool = False
    is_versus: bool = False
    max_score: int | None = Field(None, gt=0)
    start_dt: dt.datetime | None = None
    end_dt: dt.datetime | None = None

    @model_validator(mode='after')
    def validate_activity_fields(self):
        validate_activity(self.is_scoreable, self.max_score, self.start_dt, self.end_dt)
        return self


class SActivityAdd(SActivityBase):
    pass


class SActivityUpdate(BaseModel):
    name: str | None = Field(None, max_length=150)
    latitude: float | None = None
    longitude: float | None = None
    is_scoreable: bool | None = None
    is_versus: bool | None = None
    max_score: int | None = Field(None, gt=0)
    start_dt: dt.datetime | None = None
    end_dt: dt.datetime | None = None


class SActivityOut(SActivityBase):
    id: int
    event_id: int
    model_config = {"from_attributes": True}


# Event
class SEvent(_EventBase):
    id: int
    media: list[SEventMedia]
    state: Literal["future", "current", "past"]
    activities: List[SActivityOut]

    model_config = {"from_attributes": True}


class SParticipationCreate(BaseModel):
    participant_type: ParticipantTypeEnum
    team_name: str | None = Field(None, min_length=1, max_length=80)


class SParticipationMemberOut(BaseModel):
    user: SUserPublic

    model_config = {"from_attributes": True}


class SParticipationOut(BaseModel):
    id: int
    event_id: int
    participant_type: ParticipantTypeEnum
    team_name: str | None
    creator: SUserPublic
    members: list[SParticipationMemberOut]

    model_config = {"from_attributes": True}
