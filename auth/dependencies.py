import uuid
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import ExpiredSignatureError, InvalidTokenError

from config import SECRET_KEY, ALGORITHM
from db.users import UserOrm
from users.repository import UserRepository

bearer_scheme = HTTPBearer()
bearer_scheme_optional = HTTPBearer(auto_error=False)


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = credentials.credentials
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise credentials_exc
        user_id = uuid.UUID(user_id_str)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (InvalidTokenError, ValueError):
        raise credentials_exc

    user = await UserRepository.get_user_by_id(user_id)
    if not user:
        raise credentials_exc

    return user


async def get_optional_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme_optional)  # Используем новую схему
) -> UserOrm | None:
    if not credentials:
        return None
    try:
        # Это почти полная копия get_current_user, но она не выбрасывает ошибку, а возвращает None
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None
        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError, AttributeError):
        return None

    user = await UserRepository.get_user_by_id(user_id)
    return user
