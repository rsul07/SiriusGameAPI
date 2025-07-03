import os
from contextlib import asynccontextmanager
from fastapi import FastAPI

from utils.migrate import create_tables, delete_tables
from events.router import router as events_router

ENV = os.getenv("ENV", "dev")

if ENV == "dev":
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await create_tables()
        yield
else:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await delete_tables()
        await create_tables()
        yield

app = FastAPI(
    lifespan=lifespan,
    debug=(ENV == "dev"),
    docs_url=None if ENV == "prod" else "/docs",
    redoc_url=None if ENV == "prod" else "/redoc",
    openapi_url=None if ENV == "prod" else "/openapi.json",
)

app.include_router(events_router)