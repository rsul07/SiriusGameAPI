import os

ENV = os.getenv("ENV", "dev")
DB_URL = (
    "sqlite+aiosqlite:///database_dev.db"
    if ENV == "dev"
    else "sqlite+aiosqlite:///database.db"
)
