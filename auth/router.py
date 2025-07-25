from fastapi import APIRouter, HTTPException, status

from auth.exceptions import UserAlreadyExistsError
from auth.security import verify_password, create_access_token
from users.repository import UserRepository
from users.schemas import SUserRegister, SUserOut, TokenOut, SLoginRequest

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


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
        login_data: SLoginRequest
):
    user = await UserRepository.get_user_by_login_identifier(login_data.login_identifier)

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token, expires_in = create_access_token(
        data={"sub": str(user.id)}
    )

    return TokenOut(access_token=access_token, expires_in=expires_in)
