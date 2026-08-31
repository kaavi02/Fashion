import logging
import ssl
import os
import shutil
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings

logger = logging.getLogger("fashion_store")
logging.basicConfig(level=logging.INFO)

connect_args = {
    "connect_timeout": 4,
    "read_timeout": 5,
    "write_timeout": 5
}
engine = None
ACTIVE_DB_TYPE = "unknown"

# Try connecting to configured primary database (MySQL)
if settings.DATABASE_URL and "mysql" in settings.DATABASE_URL.lower():
    try:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx

        candidate_engine = create_engine(
            settings.DATABASE_URL,
            connect_args=connect_args,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=280,
            pool_timeout=5,
        )
        # Test connection quickly
        with candidate_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine = candidate_engine
        ACTIVE_DB_TYPE = "MySQL"
        logger.info("Successfully connected to MySQL database: %s", settings.DB_HOST)
    except Exception as exc:
        logger.warning(
            f"[DATABASE NOTICE] Unable to reach MySQL server at '{settings.DB_HOST}': {exc}. "
            "Activating resilient local SQLite fallback so the application runs seamlessly."
        )

# If MySQL could not connect, fallback to SQLite
if engine is None:
    import shutil
    from pathlib import Path
    
    source_db = Path(__file__).resolve().parent.parent.parent.parent / "fashion_store.db"
    
    # On serverless platforms like Vercel, the source directory (/var/task) is read-only.
    # The /tmp directory is the only writable storage. Copy DB to /tmp if available.
    target_db = source_db
    tmp_dir = Path("/tmp")
    if tmp_dir.exists() and os.access(tmp_dir, os.W_OK):
        tmp_db = tmp_dir / "fashion_store.db"
        if not tmp_db.exists() and source_db.exists():
            try:
                shutil.copy2(source_db, tmp_db)
                logger.info("Copied database to writable /tmp storage: %s", tmp_db)
            except Exception as copy_err:
                logger.warning("Failed to copy database to /tmp: %s", copy_err)
        if tmp_db.exists():
            target_db = tmp_db

    fallback_url = f"sqlite:///{target_db.as_posix()}"
    engine = create_engine(
        fallback_url,
        connect_args={"check_same_thread": False}
    )
    ACTIVE_DB_TYPE = "SQLite (Resilient Fallback)"
    logger.info("Application initialized with SQLite fallback engine: %s", fallback_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Provides a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
