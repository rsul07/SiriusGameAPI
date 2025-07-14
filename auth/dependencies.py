import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from config import SECRET_KEY, ALGORITHM
from users.repository import UserRepository

bearer_scheme = HTTPBearer()


async def get_current_user(token: str = Depends(bearer_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    user = await UserRepository.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user
