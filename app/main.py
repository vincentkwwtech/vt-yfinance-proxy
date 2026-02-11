from __future__ import annotations

from fastapi import FastAPI

from app.routers import market


app = FastAPI(title="VT YFinance Proxy", version="0.1.0")

app.include_router(market.router, prefix="/api/v1", tags=["market"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
