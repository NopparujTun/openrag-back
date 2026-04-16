from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import bots, chat, documents


app = FastAPI(title="YourBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    # Allow the known frontend origin WITH credentials (for authenticated routes)
    # AND allow all origins for the public embed (without credentials)
    allow_origins=["*"],
    allow_credentials=False,   # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bots.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"ok": True}

