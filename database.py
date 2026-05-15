"""
Database connection and session management.
Ensures proper resource cleanup to prevent connection pool exhaustion.
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./market_pulse.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    pool_pre_ping=True  # Verify connection before using
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Get database session with automatic cleanup.
    
    Ensures connections are returned to pool even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        raise e
    finally:
        try:
            db.close()
        except Exception:
            pass


@contextmanager
def get_db_context():
    """Context manager for database sessions.
    
    Preferred for scripts and background jobs.
    Ensures proper resource cleanup.
    
    Usage:
        with get_db_context() as db:
            # do work
            db.commit()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        raise e
    finally:
        try:
            db.close()
        except Exception:
            pass


def close_database():
    """Close all database connections.
    
    Call this during application shutdown.
    """
    try:
        engine.dispose()
    except Exception as e:
        print(f"Error closing database: {e}")
