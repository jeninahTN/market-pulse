"""
Shared HTTP client with proper connection pooling and resource cleanup.
Prevents connection pool exhaustion after extended operation.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class HTTPClientManager:
    """Manages HTTP client with connection pooling and proper cleanup"""
    
    _session: Optional[requests.Session] = None
    
    @classmethod
    def get_session(cls) -> requests.Session:
        """Get or create session with connection pooling"""
        if cls._session is None:
            cls._session = cls._create_session()
        return cls._session
    
    @classmethod
    def _create_session(cls) -> requests.Session:
        """Create session with retry strategy and connection pooling"""
        session = requests.Session()
        
        # Retry strategy: retry on connection errors and timeouts
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD", "POST"]
        )
        
        # Mount adapter with connection pooling
        # pool_connections: number of connection pools to cache
        # pool_maxsize: number of connections in pool
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # User agent
        session.headers.update({
            "User-Agent": "Market-Pulse/1.0 (agricultural-forecast)"
        })
        
        logger.info("HTTP session created with connection pooling")
        return session
    
    @classmethod
    def close_session(cls):
        """Close session to release connections"""
        if cls._session:
            try:
                cls._session.close()
                cls._session = None
                logger.info("HTTP session closed, connections released")
            except Exception as e:
                logger.error(f"Error closing HTTP session: {e}")
    
    @classmethod
    def get(cls, url: str, timeout: int = 30, **kwargs):
        """Safe GET request with timeout"""
        session = cls.get_session()
        try:
            return session.get(url, timeout=timeout, **kwargs)
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url} (timeout={timeout}s)")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"HTTP request failed for {url}: {e}")
            raise
    
    @classmethod
    def post(cls, url: str, timeout: int = 30, **kwargs):
        """Safe POST request with timeout"""
        session = cls.get_session()
        try:
            return session.post(url, timeout=timeout, **kwargs)
        except requests.exceptions.Timeout:
            logger.error(f"POST request timeout for {url} (timeout={timeout}s)")
            raise
        except Exception as e:
            logger.error(f"HTTP POST request failed for {url}: {e}")
            raise


# Singleton instance for global use
http_client = HTTPClientManager()
