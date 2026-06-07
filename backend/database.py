import os
import re
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Use SQLite for local development by default, but allow overriding with DATABASE_URL
default_db = "sqlite:////tmp/sql_app.db" if os.getenv("VERCEL") == "1" else "sqlite:///./sql_app.db"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", default_db)

# Debug: print sanitized URL (hide password)
sanitized = re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", SQLALCHEMY_DATABASE_URL)
print(f"Database URL: {sanitized}")

# SQLite needs check_same_thread=False
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # Test connections before using them
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

