import os
from pathlib import Path

ENV = os.getenv("ENV", "dev") # dev режим для локального запуска. на сервере всегда используется prod
SERVER_IP = "62.183.4.195"

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "sirius148*")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", SERVER_IP)
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "dev_db")

if POSTGRES_PASSWORD is None:
    raise ValueError("POSTGRES_PASSWORD не определен")

DB_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = os.getenv("SECRET_KEY",
                       "yRvebEaFw2Oihv6e9MY0MZkhkvd7yhA-cG7PtSIjooFQooo7Oj2FugKYfL_39yXnr7B84Eg1r8l-EWbpkCA8Kw")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1488

if ENV == "dev":
    MEDIA_DIR = BASE_DIR / "media"
else:
    MEDIA_DIR = Path("/media")

AVATAR_DIR = MEDIA_DIR / "avatars"

Path(MEDIA_DIR).mkdir(parents=True, exist_ok=True)
Path(AVATAR_DIR).mkdir(parents=True, exist_ok=True)