"""
main.py
=======
FastAPI Application Entry Point for Backend 2.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import BackendException
from app.api.routes import health, datasets, database, evaluations, results, agents

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    settings.init_directories()
    yield
    logger.info("Shutting down Backend 2")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In local development, accessible by Backend 1 and Frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(BackendException)
async def backend_exception_handler(request: Request, exc: BackendException):
    logger.error(f"Domain Exception: {exc.message} ({exc.details})")
    return JSONResponse(
        status_code=400,
        content={"error": exc.message, "details": exc.details}
    )

# Mount Routes
app.include_router(health.router)
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(database.router, prefix="/api/v1")
app.include_router(evaluations.router, prefix="/api/v1")
app.include_router(results.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
