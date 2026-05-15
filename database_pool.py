"""
Database connection pooling for better performance and resource management.
Prevents connection pool exhaustion after extended operation.
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./market_pulse.db")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    pool_pre_ping=True,  # Test connections before using them
    echo=False  # Set to True for SQL debugging
)

# Create session factory with scoped session for thread safety
SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False
    )
)

def get_db():
    """Get database session with automatic cleanup.
    
    Used as dependency in FastAPI endpoints.
    Ensures proper cleanup even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        # Rollback on any exception
        try:
            db.rollback()
        except Exception:
            pass
        raise e
    finally:
        # Always close the session
        try:
            db.close()
        except Exception:
            pass


@contextmanager
def get_db_context():
    """Context manager for database sessions.
    
    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
            db.commit()  # Explicit commit
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        # Rollback on exception
        try:
            db.rollback()
        except Exception:
            pass
        raise e
    finally:
        # Always close
        try:
            db.close()
        except Exception:
            pass


def close_db_connection():
    """Explicitly close database connection pool.
    
    Use this when shutting down the application to release
    all database connections and connections handles.
    """
    try:
        SessionLocal.remove()
        engine.dispose()
    except Exception as e:
        print(f"Error closing database connection: {e}")
