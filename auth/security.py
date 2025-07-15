import datetime
import jwt
from passlib.context import CryptContext

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, совпадает ли обычный пароль с хешированным."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Возвращает хеш для пароля."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta_minutes: int | None = None) -> tuple[str, int]:
    """
    Создает JWT-токен и возвращает его вместе со сроком жизни в секундах.
    """
    to_encode = data.copy()

    if expires_delta_minutes:
        expire_delta = datetime.timedelta(minutes=expires_delta_minutes)
    else:
        expire_delta = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.datetime.now(datetime.timezone.utc) + expire_delta
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    expires_in_seconds = int(expire_delta.total_seconds())

    return encoded_jwt, expires_in_seconds
