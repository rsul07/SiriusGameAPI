import os
from pathlib import Path

ENV = os.getenv("ENV", "dev")

if ENV == "prod":
    db_path = "/data/database.db"
else:
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "data" / "database_dev.db"
    db_path.parent.mkdir(exist_ok=True)

DB_URL = f"sqlite+aiosqlite:///{db_path}"
