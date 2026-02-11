from __future__ import annotations

import logging
import os

from fastapi import FastAPI

from app.routers import market


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(title="VT YFinance Proxy", version="0.1.0")

app.include_router(market.router, prefix="/api/v1", tags=["market"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
