from fastapi import APIRouter
from typing import Dict, Any
from app.config import settings

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint to verify backend status.
    """
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENV,
        "version": "0.1.0"
    }
