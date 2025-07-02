import datetime
from enum import Enum as PyEnum
from sqlalchemy import Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from . import Model

class StateEnum(str, PyEnum):
    past = "past"
    current = "current"
    future = "future"

class TypeEnum(str, PyEnum):
    individual = "individual"
    team = "team"

class EventOrm(Model):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column()
    date: Mapped[datetime.datetime] = mapped_column()
    state: Mapped[StateEnum] = mapped_column(SQLEnum(StateEnum))
    type: Mapped[TypeEnum] = mapped_column(SQLEnum(TypeEnum))
    rules: Mapped[dict | None] = mapped_column(JSON)
