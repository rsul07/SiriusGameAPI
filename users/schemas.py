import datetime
import re
import uuid
from pydantic import BaseModel, EmailStr, Field, field_validator
from db.users import GenderEnum, RoleEnum

PHONE_REGEX = r"^\+?[1-9]\d{1,14}$"


class SUserRegister(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    phone: str = Field(..., max_length=18)
    password: str = Field(..., min_length=6, max_length=50)
    birthday: datetime.date
    gender: GenderEnum

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not re.match(PHONE_REGEX, value):
            raise ValueError("Некорректный формат номера телефона.")
        return value


class SLoginRequest(BaseModel):
    login_identifier: str = Field(..., description="Email or Phone number")
    password: str


class SUserOut(BaseModel):
    id: uuid.UUID
    handle: str
    email: EmailStr
    full_name: str
    avatar_url: str | None = None
    phone: str
    gender: GenderEnum
    birthday: datetime.date
    height_cm: int | None = None
    weight_kg: float | None = None
    is_verified: bool
    is_2fa_enabled: bool
    role: RoleEnum

    model_config = {"from_attributes": True}


class SUserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=3, max_length=100)
    avatar_url: str | None = Field(None, max_length=255)
    height_cm: int | None = Field(None, gt=0, description="Рост в сантиметрах")
    weight_kg: float | None = Field(None, gt=0, description="Вес в килограммах")
    birthday: datetime.date | None = None
    gender: GenderEnum | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class SPasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=50)


class SUserPublic(BaseModel):
    """
    Схема для публичного отображения данных пользователя.
    Не содержит email, телефон и другую личную информацию.
    """
    id: uuid.UUID
    handle: str
    full_name: str
    avatar_url: str | None = None

    model_config = {"from_attributes": True}