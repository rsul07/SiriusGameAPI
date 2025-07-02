from fastapi import FastAPI
from contextlib import asynccontextmanager

from utils.migrate import create_tables, delete_tables

from events.router import router as events_router

class Settings():
    debug_mode: bool = True

settings = Settings()

if settings.debug_mode:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await create_tables()
        print("Tables created")
        yield
else:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await delete_tables()
        print("Tables deleted")
        await create_tables()
        print("Tables created")
        yield

app = FastAPI(lifespan=lifespan, debug=True)

app.include_router(events_router)
# app.include_router(teams_router)
# app.include_router(pushes_router)