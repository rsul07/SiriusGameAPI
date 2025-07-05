import datetime as dt
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, computed_field, model_validator
from db.events import MediaEnum

class _EventMedia(BaseModel):
    url: str
    media_type: MediaEnum = MediaEnum.image
    name: Optional[str]
    order: int = 0  # used by image slider

class SEventMediaAdd(_EventMedia):
    pass

class SEventMedia(_EventMedia):
    id: int
    event_id: int

    model_config = {"from_attributes": True}

class EventExtrasMixin(BaseModel):
    description: Optional[str] = None
    start_time: Optional[dt.time] = None
    end_time: Optional[dt.time] = None
    max_members: Optional[int] = None
    max_teams: Optional[int] = None

    @model_validator(mode="after")
    def validate_limits(self):
        if not hasattr(self, "is_team"):
            return self
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

class SEventAdd(_EventBase):
    pass

class SEventUpdate(EventExtrasMixin):
    title: Optional[str] = Field(None, max_length=120)
    date: Optional[dt.date] = None
    is_team: Optional[bool] = None

class SEventId(BaseModel):
    ok: bool = True
    event_id: int

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