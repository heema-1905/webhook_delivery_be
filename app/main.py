import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.exceptions import HTTPException, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.webhooks import webhook_router
from app.config.database import close_db_client, init_db_client
from app.config.indexes import CreateDbCollectionIndexes
from app.config.settings import settings
from app.schemas.base import HealthCheck
from app.utils.custom_exception_handlers import (
    authentication_exception_handler,
    global_exception_handler,
    http_exception_handler,
    response_validation_exception_handler,
    utils_exception_handler,
    webhook_event_exception_handler,
)
from app.utils.exceptions.core import AuthenticationException, UtilsException
from app.utils.exceptions.webhooks import WebhookEventException

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(name)s | %(message)s",
)


logger = logging.getLogger(__name__)
logger.propagate = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""

    logger.info("Application startup initiated")
    try:
        await init_db_client()
    except Exception:
        logger.exception("MongoDB initialization failed during startup")
        raise
    # Creating db indexes for all db collections
    index_creator = CreateDbCollectionIndexes()
    await index_creator.create_all_collections_indexes()

    yield
    # Shutdown
    await close_db_client()
    logger.info("Application shutdown completed")


app = FastAPI(
    debug=settings.DEBUG,
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_allowed_settings.allowed_origins,
    allow_headers=settings.get_cors_allowed_settings.allowed_headers,
    allow_methods=settings.get_cors_allowed_settings.allowed_methods,
    allow_credentials=True,
)

app.add_exception_handler(
    AuthenticationException, handler=authentication_exception_handler
)
app.add_exception_handler(UtilsException, handler=utils_exception_handler)
app.add_exception_handler(
    WebhookEventException, handler=webhook_event_exception_handler
)
app.add_exception_handler(
    ResponseValidationError, handler=response_validation_exception_handler
)
app.add_exception_handler(HTTPException, handler=http_exception_handler)
app.add_exception_handler(Exception, handler=global_exception_handler)


@app.get(
    "/health",
    tags=["Healthcheck"],
    summary="Perform a health check",
    response_description="Return HTTP status code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
async def get_health() -> dict:
    """Returns the health check status of the API routes"""
    return {"status": "OK"}


app.include_router(router=webhook_router)
