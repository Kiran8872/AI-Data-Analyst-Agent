from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, LargeBinary
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz

from database import Base

def get_now():
    return datetime.now(pytz.UTC)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_now)

    datasets = relationship("Dataset", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    size_bytes = Column(Integer)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=get_now)

    owner = relationship("User", back_populates="datasets")
    reports = relationship("AnalysisReport", back_populates="dataset")
    file_record = relationship("DatasetFile", back_populates="dataset", uselist=False, cascade="all, delete-orphan")


class DatasetFile(Base):
    __tablename__ = "dataset_files"

    dataset_id = Column(Integer, ForeignKey("datasets.id"), primary_key=True)
    content = Column(LargeBinary, nullable=False)
    updated_at = Column(DateTime, default=get_now, onupdate=get_now)

    dataset = relationship("Dataset", back_populates="file_record")


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    summary = Column(String)
    metrics_json = Column(String) # Store JSON as string for SQLite compatibility
    charts_json = Column(String) # Store JSON as string
    created_at = Column(DateTime, default=get_now)

    dataset = relationship("Dataset", back_populates="reports")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    details = Column(String)
    latency_ms = Column(Float)
    cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=get_now)

    user = relationship("User", back_populates="audit_logs")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    dataset_ids = Column(String, nullable=True) # Comma-separated list of dataset IDs
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String, nullable=False) # 'user' or 'ai'
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=get_now)
