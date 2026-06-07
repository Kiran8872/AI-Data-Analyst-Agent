from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import datetime

import models, auth, database

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)

from typing import List, Optional

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    details: str
    latency_ms: Optional[float] = None
    cost_usd: Optional[float] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    # Fetch latest 100 audit logs
    logs = db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(100).all()
    return logs

@router.get("/stats")
def get_system_stats(
    current_user: models.User = Depends(auth.get_current_admin_user),
    db: Session = Depends(database.get_db)
):
    user_count = db.query(models.User).count()
    dataset_count = db.query(models.Dataset).count()
    query_count = db.query(models.AuditLog).filter(models.AuditLog.action == "CHAT_QUERY").count()
    
    return {
        "total_users": user_count,
        "total_datasets": dataset_count,
        "total_queries": query_count,
        "status": "Healthy"
    }
