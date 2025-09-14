from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import get_db
from pydantic import BaseModel
from datetime import datetime
import os

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str
    version: str
    uptime: str

@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify service status and database connectivity.
    """
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        database_status = "healthy"
    except Exception as e:
        database_status = f"unhealthy: {str(e)}"
    
    # Determine overall status
    if database_status == "healthy":
        status = "healthy"
    else:
        status = "unhealthy"
    
    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow(),
        database=database_status,
        version="1.0.0",
        uptime="N/A"  # In a real implementation, you'd track this
    )

@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check for Kubernetes/Docker health checks.
    Returns 200 if ready to serve traffic, 503 if not.
    """
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/Docker health checks.
    Returns 200 if the service is alive.
    """
    return {"status": "alive"}
