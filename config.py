import os
from pathlib import Path

ENV = os.getenv("ENV", "dev")
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = Path("/data")
db_path = DATA_DIR / "database.db"

SECRET_KEY = os.getenv("SECRET_KEY",
                       "yRvebEaFw2Oihv6e9MY0MZkhkvd7yhA-cG7PtSIjooFQooo7Oj2FugKYfL_39yXnr7B84Eg1r8l-EWbpkCA8Kw")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1488

DB_URL = f"sqlite+aiosqlite:///{db_path}"
MEDIA_DIR = DATA_DIR / "media"
AVATAR_DIR = MEDIA_DIR / "avatars"

Path(MEDIA_DIR).mkdir(parents=True, exist_ok=True)
Path(AVATAR_DIR).mkdir(parents=True, exist_ok=True)