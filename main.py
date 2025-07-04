from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.migrate import create_tables, delete_tables
from events.router import router as events_router
from config import ENV

if ENV == "dev":
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await create_tables()
        yield
else:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await create_tables()
        yield

app = FastAPI(
    lifespan=lifespan,
    debug=(ENV == "dev"),
    docs_url=None if ENV == "prod" else "/docs",
    redoc_url=None if ENV == "prod" else "/redoc",
    openapi_url=None if ENV == "prod" else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events_router)