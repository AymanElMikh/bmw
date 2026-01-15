"""
Application Factory for FastAPI
Creates and configures the FastAPI application instance
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime

# Import configuration
from configs.config import settings, config

# Import database
from src.database import init_db, get_db

# Import repositories
from src.database import (
    UserRepository, ClauseRepository, TicketRepository,
    InvoiceRepository, AuditRepository
)

# Import services
from src.services.jira_integration import JiraIntegrationService
from src.services.mapping_engine import MappingEngine
from src.services.invoice_generator import InvoiceGenerator

# Import routes
from src.routes import (
    register_user_routes,
    register_clause_routes,
    register_jira_routes,
    register_invoice_routes,
    register_audit_routes
)


def configure_logging():
    """Configure application logging"""
    os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
    logger.info(f"Environment: {os.environ.get('ENV', 'development')}")
    logger.info(f"Debug mode: {config.DEBUG}")
    logger.info(f"Database: {config.DATABASE_URL}")
    logger.info(f"CORS origins: {config.CORS_ORIGINS}")
    
    return logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown
    """
    # Startup
    logger = logging.getLogger(__name__)
    
    # Ensure required directories exist
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)
    
    # Initialize database
    init_db()
    logger.info("[OK] Database initialized")
    logger.info(f"[OK] Upload directory: {config.UPLOAD_DIR}")
    logger.info(f"[OK] SSO enabled: {config.SSO_ENABLED}")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    """
    Application factory function.
    Creates and configures the FastAPI application.
    """
    # Configure logging first
    logger = configure_logging()
    
    # Create FastAPI app
    app = FastAPI(
        title=config.APP_NAME,
        description=settings.application.description,
        version=config.APP_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        debug=config.DEBUG,
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store services in app state for dependency injection
    app.state.jira_service = JiraIntegrationService
    app.state.mapping_engine = MappingEngine
    app.state.invoice_generator = InvoiceGenerator
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register routes
    register_routes(app)
    
    # Health check endpoints
    @app.get("/", tags=["Health"])
    async def root():
        return {
            "service": config.APP_NAME,
            "status": "operational",
            "version": config.APP_VERSION,
            "timestamp": datetime.now().isoformat()
        }
    
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    
    logger.info("[OK] Application configured successfully")
    
    return app


def register_routes(app: FastAPI):
    """Register all application routes"""
    register_user_routes(app)
    register_clause_routes(app)
    register_jira_routes(app)
    register_invoice_routes(app)
    register_audit_routes(app)


def register_error_handlers(app: FastAPI):
    """Register global error handlers"""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        logger = logging.getLogger(__name__)
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal server error",
                "details": str(exc) if config.DEBUG else "An error occurred"
            }
        )


# Export create_app as the main factory
__all__ = ['create_app']