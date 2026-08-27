from fastapi import APIRouter

from app.api.v1.health import (
    router as health_router,
)
from app.api.v1.orders import (
    router as orders_router,
)
from app.api.v1.risks import (
    router as risks_router,
)
from app.api.v1.suppliers import (
    router as suppliers_router,
)
from app.api.v1.tickets import (
    router as tickets_router,
)


api_router = APIRouter()


api_router.include_router(
    health_router
)

api_router.include_router(
    suppliers_router
)

api_router.include_router(
    orders_router
)

api_router.include_router(
    risks_router
)

api_router.include_router(
    tickets_router
)