from neurocache.utils.logging import RequestLogContext, setup_logging

# setup logging, before importing anything else (and before creating other loggers)
log_context_var = setup_logging()

import argparse
import json
import logging
import uuid
from typing import Awaitable, Callable

import starlette.requests
import uvicorn
from fastapi import FastAPI, Request, Response  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware

from neurocache.core.config import get_settings
from neurocache.routers.main import api_router

config = get_settings()

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Neurocache",
    openapi_url=f"{config.API_PREFIX}/openapi.json",
    docs_url=f"{config.API_PREFIX}/docs",
)


def _get_allowed_origins() -> list[str]:
    return config.ALLOWED_ORIGINS.get(config.ENVIRONMENT, config.ALLOWED_ORIGINS["development"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix=config.API_PREFIX)


@app.middleware("http")
async def log_request(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    # Skip logging for noisy endpoints
    url_path = str(request.url.path)
    noisy_patterns = ["/api/health/", "/api/health"]
    try:
        body = await request.body()
        extra = {"body": body, "headers": request.headers}
    except starlette.requests.ClientDisconnect:
        logger.warning("Client disconnected during request body read", exc_info=True)
        extra = {"headers": request.headers}
    if not any(url_path.endswith(pattern) for pattern in noisy_patterns) and request.method != "OPTIONS":
        logger.info(f"Request: {request.method} {request.url}", extra=extra)
    return await call_next(request)


@app.middleware("http")
async def add_request_context(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    request_json = None
    try:
        request_json = await request.json()
    except starlette.requests.ClientDisconnect:
        logger.warning("Client disconnected during request body JSON parsing", exc_info=True)
    except json.JSONDecodeError:
        pass

    token = log_context_var.set(RequestLogContext(request_id=uuid.uuid4(), request=request, request_json=request_json))
    response = await call_next(request)

    log_context_var.reset(token)
    return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")

    args = parser.parse_args()

    uvicorn.run(
        "neurocache.app:app",
        host="127.0.0.1",
        port=args.port,
        reload=args.reload,
    )
