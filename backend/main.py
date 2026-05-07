import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import ingest, tickets, voice
from services.briefing_generator import warmup_on_startup


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    asyncio.create_task(warmup_on_startup())
    yield


app = FastAPI(title="Nava — AI Triage System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(tickets.router)
app.include_router(voice.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
