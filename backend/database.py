import os
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

# Use SQLite for local development by default, but allow overriding with DATABASE_URL
default_db = "sqlite:////tmp/sql_app.db" if os.getenv("VERCEL") == "1" else "sqlite:///./sql_app.db"
raw_database_url = os.getenv("DATABASE_URL", default_db)

def normalize_database_url(database_url: str):
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    url = make_url(database_url)
    if url.drivername.startswith("postgresql"):
        query = dict(url.query)
        query.setdefault("sslmode", "require")
        url = url.set(query=query)
    return url

SQLALCHEMY_DATABASE_URL = normalize_database_url(raw_database_url)

# Debug: print sanitized URL (hide password)
print(f"Database URL: {SQLALCHEMY_DATABASE_URL.render_as_string(hide_password=True)}")

# SQLite needs check_same_thread=False
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.drivername.startswith("sqlite") else {}

engine_kwargs = {
    "connect_args": connect_args,
    "pool_pre_ping": True,
}

if SQLALCHEMY_DATABASE_URL.drivername.startswith("postgresql"):
    # Supabase transaction pooler uses port 6543 and should not be double-pooled
    # by SQLAlchemy.
    if SQLALCHEMY_DATABASE_URL.host and SQLALCHEMY_DATABASE_URL.host.endswith(".pooler.supabase.com") and SQLALCHEMY_DATABASE_URL.port == 6543:
        engine_kwargs["poolclass"] = NullPool
    else:
        engine_kwargs.update(
            {
                "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
                "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
                "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
            }
        )

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    **engine_kwargs,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
