
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import audio, assumptions, graph, scenarios


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AssumptionGraph API",
    description="Enterprise Assumption Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan
)

# Register API routers
app.include_router(audio.router)
app.include_router(assumptions.router)
app.include_router(graph.router)
app.include_router(scenarios.router)

# Configure frontend access
frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "project": "AssumptionGraph",
        "status": "running",
        "message": "Enterprise Assumption Intelligence API"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
