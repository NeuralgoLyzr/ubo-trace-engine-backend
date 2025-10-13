"""
UBO Trace Engine Backend - Main Application
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn

from utils.settings import settings
from utils.database import connect_to_mongo, close_mongo_connection
from api.endpoints import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="UBO Trace Engine Backend API for Ultimate Beneficial Owner tracing using AI agents",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router, prefix="/api/v1", tags=["ubo-trace"])

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting UBO Trace Engine Backend...")
    try:
        await connect_to_mongo()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down UBO Trace Engine Backend...")
    await close_mongo_connection()
    logger.info("Application shutdown completed")

@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "message": "UBO Trace Engine Backend API",
        "status": "running",
        "version": settings.version,
        "docs": "/docs"
    }

@app.get("/health", tags=["health"])
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "ubo_trace_engine_backend",
        "version": settings.version
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
