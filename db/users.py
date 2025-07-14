import datetime
import uuid
from enum import Enum

from sqlalchemy import String, Date, Boolean, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from db import Model


class GenderEnum(str, Enum):
    male = "male"
    female = "female"


class RoleEnum(str, Enum):
    user = "user"
    organizer = "organizer"
    admin = "admin"


class UserOrm(Model):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    handle: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(18), unique=True)
    birthday: Mapped[datetime.date] = mapped_column(Date)
    gender: Mapped[GenderEnum]

    height_cm: Mapped[int | None]
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2))

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    role: Mapped[RoleEnum] = mapped_column(default=RoleEnum.user, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(), nullable=False)
