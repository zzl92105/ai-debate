from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.debate import router as debate_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="AI Debate API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(debate_router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

