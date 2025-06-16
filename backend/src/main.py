from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from typing import Dict, Any

# Import scheduler functions
from src.core.scheduler import start_scheduler, shutdown_scheduler

# Import configuration
from src.core.config import settings

# Import routers
from src.auth import routes as auth_routes
from src.campaigns import routes as campaign_routes
from src.followups import routes as followup_routes
from src.llm import routes as llm_routes
from src.users import routes as user_routes
from src.ai_chat import routes as ai_chat_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown logic"""
    try:
        # Startup logic
        logger.info("Starting application...")
        
        # Initialize database connection
        from src.core.config.database import engine, Base
        logger.info("Creating database tables if they don't exist...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Start scheduler
        logger.info("Starting scheduler...")
        start_scheduler()
        
        logger.info("Application startup completed successfully")
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        # Shutdown logic
        try:
            logger.info("Shutting down application...")
            shutdown_scheduler()
            logger.info("Scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")

def create_application() -> FastAPI:
    """Creates and configures the FastAPI application"""
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-Powered Email Outreach Platform API",
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # Add middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Include routers with versioning
    api_prefix = "/api/v1"
    app.include_router(
        auth_routes.router,
        prefix=f"{api_prefix}/auth",
        tags=["Authentication"]
    )
    app.include_router(
        campaign_routes.router,
        prefix=f"{api_prefix}/campaigns",
        tags=["Campaigns"]
    )
    app.include_router(
        followup_routes.router,
        prefix=f"{api_prefix}/followups",
        tags=["Follow-ups"]
    )
    app.include_router(
        llm_routes.router,
        prefix=f"{api_prefix}/llm",
        tags=["LLM"]
    )
    app.include_router(
        user_routes.router,
        prefix=f"{api_prefix}/users",
        tags=["Users"]
    )
    app.include_router(
        ai_chat_routes.router,
        prefix=f"{api_prefix}/ai-chat",
        tags=["AI Chat & Email Style"]
    )

    return app

# Create FastAPI instance
app = create_application()

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV
    }

# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI-Powered Email Outreach Platform API",
        "docs_url": "/api/docs",
        "environment": settings.APP_ENV
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_ENV == "development",
        workers=4
    )
