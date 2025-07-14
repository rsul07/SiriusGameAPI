import datetime
import uuid
from pydantic import BaseModel, EmailStr, Field

from db.users import GenderEnum


class SUserRegister(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(..., max_length=18)
    password: str = Field(..., min_length=6, max_length=50)
    birthday: datetime.date
    gender: GenderEnum


class SUserOut(BaseModel):
    id: uuid.UUID
    handle: str
    email: EmailStr
    full_name: str
    avatar_url: str | None = None
    phone: str
    gender: GenderEnum
    birthday: datetime.date

    model_config = {"from_attributes": True}
