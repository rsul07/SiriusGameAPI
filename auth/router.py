from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from users.repository import UserRepository
from users.schemas import SUserRegister, SUserOut
from auth.security import verify_password, create_access_token
from auth.exceptions import UserAlreadyExistsError

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post(
    "/register",
    response_model=SUserOut,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(user_data: SUserRegister):
    try:
        new_user = await UserRepository.create_user(user_data)
        return new_user
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email или телефоном уже существует.",
        )


@router.post("/login", response_model=TokenOut)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = await UserRepository.get_user_by_email(form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, expires_in = create_access_token(
        data={"sub": str(user.id)}
    )

    return TokenOut(access_token=access_token, expires_in=expires_in)
