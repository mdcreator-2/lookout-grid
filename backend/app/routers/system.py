from fastapi import APIRouter, status, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {
  "status": "healthy",
  "timestamp": "2026-08-24T13:00:00+05:30",
  "database": "unknown",
  "mqtt": "unknown"
}