from fastapi import FastAPI

from app.api.agent import (
    router as agent_router,
)
from app.api.health import (
    router as health_router,
)
from app.observability.logging import (
    configure_logging,
)


configure_logging()


app = FastAPI(
    title="EnterpriseOps Agent",
    version="1.0.0",
    description=(
        "Production-oriented enterprise "
        "operations AI agent."
    ),
)


app.include_router(
    health_router
)

app.include_router(
    agent_router
)