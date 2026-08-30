from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.logger import setup_logging, get_logger
from app.api import endpoints

# Setup logging
setup_logging(level=settings.LOG_LEVEL, json_format=settings.LOG_JSON)
logger = get_logger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting VoiceHire Backend API", extra={
        "project": settings.PROJECT_NAME,
        "env": settings.ENV,
        "host": settings.HOST,
        "port": settings.PORT
    })
    yield
    # Shutdown logic
    logger.info("Shutting down VoiceHire Backend API")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for VoiceHire - Realtime AI Technical Interviewer",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(endpoints.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENV == "development"
    )
