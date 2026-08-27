from fastapi import FastAPI

from app.api.v1.router import (
    api_router,
)
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Enterprise procurement and "
        "operations backend service."
    ),
)


app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get("/")
def root():

    return {
        "service": settings.app_name,
        "message": (
            "EnterpriseOps Agent "
            "backend is running."
        ),
        "docs": "/docs",
    }