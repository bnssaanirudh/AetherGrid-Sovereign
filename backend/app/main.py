import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import health, snapshots, models, scenarios, admin
from .worker import start_worker, stop_worker

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AetherGridAPI")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start local background worker thread
    logger.info("Initializing operational backend dependencies...")
    start_worker()
    yield
    # Shutdown: Stop worker thread
    logger.info("Cleaning up operational backend dependencies...")
    stop_worker()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Operational API platform for the AetherGrid-Sovereign cascade prediction system.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS and Security Headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Size Limit Middleware (Work Package D)
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    # Limit max request body size to 10MB to protect worker memory
    MAX_SIZE = 10 * 1024 * 1024
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_SIZE:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "Request body size exceeds the allowed limit of 10MB."}
        )
    return await call_next(request)

# Include versioned API routers
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["System Status"])
app.include_router(snapshots.router, prefix=settings.API_V1_STR, tags=["Ingestion & Snapshots"])
app.include_router(models.router, prefix=settings.API_V1_STR, tags=["Model Serving"])
app.include_router(scenarios.router, prefix=settings.API_V1_STR, tags=["Scenarios & Predictions"])
app.include_router(admin.router, prefix=settings.API_V1_STR, tags=["Administrative Operations"])
