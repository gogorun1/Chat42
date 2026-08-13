from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import ai, auth, health, notifications, oauth, sightings, websocket, search, analytics

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(ai.router)
app.include_router(sightings.router)
app.include_router(notifications.router)
app.include_router(websocket.router)
app.include_router(search.router)
app.include_router(analytics.router)