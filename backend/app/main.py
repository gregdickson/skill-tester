from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.integrations.openrouter import OpenRouterClient
from app.integrations.brave_search import BraveSearchClient
from app.routers import companies, networks, components, training, outputs, chat, activity, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.openrouter = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        default_model=settings.default_model,
    )
    app.state.brave = BraveSearchClient(api_key=settings.brave_api_key)
    yield


app = FastAPI(title="MicroGrad Skill Optimiser", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(networks.router, prefix="/api/networks", tags=["networks"])
app.include_router(components.router, prefix="/api/networks", tags=["components"])
app.include_router(training.router, prefix="/api/networks", tags=["training"])
app.include_router(outputs.router, prefix="/api/networks", tags=["outputs"])
app.include_router(chat.router, prefix="/api/networks", tags=["chat"])
app.include_router(activity.router, prefix="/api/networks", tags=["activity"])
app.include_router(websocket.router, tags=["websocket"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
