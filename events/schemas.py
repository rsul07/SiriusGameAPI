from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, validator, field_validator, computed_field

class TypeEnum(str, Enum):
    individual = "individual"
    team = "team"

class _EventBase(BaseModel):
    name: str = Field(..., max_length=120)
    description: Optional[str] = None
    date: datetime
    type: TypeEnum
    rules: Optional[Dict[str, Any]] = None

    @validator("name", pre=True)
    def strip_name(cls, v: str) -> str:
        return v.strip()

    @field_validator('date', mode='before')
    def parse_ddmmyyyy(cls, v):
        if isinstance(v, str):
            return datetime.strptime(v, "%d.%m.%Y")
        return v

class SEventAdd(_EventBase):
    pass

class SEventUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = None
    date: Optional[datetime] = None
    type: Optional[TypeEnum] = None
    rules: Optional[Dict[str, Any]] = None

class SEvent(SEventAdd):
    id: int

    model_config = {"from_attributes": True}

    @computed_field
    def state(self) -> str:
        now = datetime.utcnow()
        if self.date.date() < now.date():
            return "past"
        if self.date > now:
            return "future"
        return "current"

class SEventId(BaseModel):
    ok: bool = True
    event_id: int