from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from events.router import router as events_router
from activities.router import events_router as event_activities_router, activities_router
from auth.router import router as auth_router
from users.router import router as users_router
from participations.router import router as participations_router
from scores.router import router as scores_router

from config import ENV, MEDIA_DIR
from utils.migrate import create_tables
from utils.seed import create_initial_users, create_initial_events, create_leaderboard_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    if ENV == "dev":
        await create_initial_users()
        await create_initial_events()
        await create_leaderboard_data()
    yield


app = FastAPI(
    lifespan=lifespan,
    debug=(ENV == "dev"),
    docs_url=None if ENV == "prod" else "/docs",
    redoc_url=None if ENV == "prod" else "/redoc",
    openapi_url=None if ENV == "prod" else "/openapi.json",
    root_path="/api"
)

app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(events_router)
app.include_router(event_activities_router)
app.include_router(activities_router)
app.include_router(participations_router)
app.include_router(scores_router)
