from __future__ import annotations

import os
import threading
import time
import concurrent.futures
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from . import models
from .database import SessionLocal, engine, get_db_context
from .refresh_state import DEFAULT_REFRESH_NAME, now_iso, record_refresh_state

KAMPALA_TZ = ZoneInfo("Africa/Kampala")
REFRESH_INTERVAL_SECONDS = int(os.getenv("MARKET_PULSE_REFRESH_INTERVAL_SECONDS", "43200"))
ENABLE_REFRESH_SCHEDULER = os.getenv("MARKET_PULSE_ENABLE_REFRESH_SCHEDULER", "1") != "0"

# Use RLock for better thread safety
_refresh_lock = threading.RLock()

# Track lock acquisition time for deadlock prevention
_lock_acquired_at: Optional[datetime] = None
_MAX_LOCK_HOLD_TIME_SECONDS = 1200  # 20 minutes max for a full refresh cycle

_scheduler_started = False


def _run_job(job_name: str, job_func: Callable[[], None], details_prefix: str) -> Tuple[str, str]:
    """Run a job with timeout and guaranteed cleanup using ThreadPoolExecutor
    
    This ensures threads are properly cleaned up even if they timeout,
    preventing daemon thread accumulation that causes unresponsiveness.
    """
    
    # Dynamic timeout based on job type
    if job_name in ['prices', 'maaif_prices']:
        timeout = 900  # 15 minutes for very slow price jobs
    elif job_name == 'sentiment':
        timeout = 600  # 10 minutes for sentiment jobs
    else:
        timeout = 300  # 5 minutes for fast jobs
    
    # Use ThreadPoolExecutor for guaranteed cleanup
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        try:
            future = executor.submit(job_func)
            # This will raise TimeoutError if job takes too long
            result = future.result(timeout=timeout)
            return "success", f"{details_prefix} completed"
        except concurrent.futures.TimeoutError:
            timeout_minutes = timeout // 60
            return "error", f"{details_prefix} timed out after {timeout_minutes} minutes"
        except Exception as exc:
            return "error", f"{details_prefix} failed: {str(exc)}"
        finally:
            # ThreadPoolExecutor cleanup is automatic when exiting context manager
            pass


def run_refresh_cycle_async() -> Dict[str, object]:
    """
    Run refresh cycle asynchronously to reduce UI lag
    Returns immediately with job status, runs in background
    """
    if not _refresh_lock.acquire(blocking=False):
        return {"status": "busy", "message": "A refresh cycle is already running."}

    # Start background thread for actual refresh
    import threading
    refresh_thread = threading.Thread(
        target=_run_refresh_cycle_background,
        daemon=True
    )
    refresh_thread.start()
    
    return {
        "status": "started",
        "message": "Refresh cycle started in background",
        "started_at": now_iso()
    }


def _run_refresh_cycle_background():
    """Run the actual refresh cycle in background"""
    try:
        # Lock is acquired by run_refresh_cycle_async(); do not re-acquire here.
        result = run_refresh_cycle(acquire_lock=False)
        print(f"Background refresh completed: {result.get('status')}")
    except Exception as e:
        print(f"Background refresh failed: {e}")
    finally:
        # Ensure lock is always released, even if the refresh failed mid-way.
        try:
            _refresh_lock.release()
        except Exception:
            pass
 

def run_refresh_cycle(*, acquire_lock: bool = True) -> Dict[str, object]:
    """
    Refresh price history, weather, sentiment, and regional signals.
    Returns a small summary dict for logging or manual runs.
    
    Includes lock timeout monitoring to prevent deadlocks.
    """
    global _lock_acquired_at
    
    lock_acquired = False
    if acquire_lock:
        # Avoid deadlocks: if a refresh is already running, return immediately.
        # Use 5 second timeout to prevent indefinite blocking
        lock_acquired = _refresh_lock.acquire(timeout=5.0)
        if not lock_acquired:
            return {"status": "busy", "message": "A refresh cycle is already running."}
        
        _lock_acquired_at = datetime.now()

    models.Base.metadata.create_all(bind=engine)
    started_at = now_iso()
    job_summaries: List[Dict[str, str]] = []

    try:
        # Monitor lock hold time to prevent deadlocks
        if _lock_acquired_at:
            elapsed = (datetime.now() - _lock_acquired_at).total_seconds()
            if elapsed > _MAX_LOCK_HOLD_TIME_SECONDS:
                raise Exception(
                    f"Lock held for {elapsed:.0f}s, exceeds maximum {_MAX_LOCK_HOLD_TIME_SECONDS}s. "
                    "This indicates a deadlock condition."
                )
        
        # Import lazily so app startup stays light and the scheduler can be reused from scripts.
        from scripts.import_prices import import_and_clean_prices
        from scripts.fetch_weather_nasa_power import fetch_weather
        from scripts.scrape_sentiment import scrape_sentiment_signals
        from scripts.process_features import process_market_features
        from scripts.export_offline_pack import export_offline_seed_pack
        from scripts.fetch_uganda_weather import UgandaWeatherFetcher
        from scripts.fetch_maaif_prices import MAAIFPriceFetcher
        from scripts.preprocess_data import preprocess_and_merge

        jobs: List[Tuple[str, Callable[[], None], str]] = [
            ("prices", import_and_clean_prices, "Price import"),
            ("maaif_prices", lambda: MAAIFPriceFetcher().fetch_all_crop_market_combinations(), "MAAIF price data"),
            ("weather_nasa", fetch_weather, "NASA POWER Weather refresh"),
            ("uganda_weather", lambda: UgandaWeatherFetcher().fetch_all_regions(), "Uganda enhanced weather"),
            ("sentiment", scrape_sentiment_signals, "Sentiment refresh"),
            ("features", process_market_features, "Regional feature refresh"),
            ("ml_preprocess", preprocess_and_merge, "ML Data Pipeline Merging"),
            ("offline_seed", export_offline_seed_pack, "Offline seed export"),
        ]

        with get_db_context() as db:
            for job_name, job_func, details_prefix in jobs:
                try:
                    status, details = _run_job(job_name, job_func, details_prefix)
                    record_refresh_state(db, job_name, status, details)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    status = "error"
                    details = f"{details_prefix} failed: {str(e)}"
                    try:
                        record_refresh_state(db, job_name, status, details)
                        db.commit()
                    except Exception:
                        pass
                
                job_summaries.append(
                    {
                        "job": job_name,
                        "status": status,
                        "details": details,
                        "refreshed_at": now_iso(),
                    }
                )

            overall_status = "success"
            if any(job["status"] != "success" for job in job_summaries):
                overall_status = "partial"

            pipeline_details = "; ".join(f"{job['job']}={job['status']}" for job in job_summaries)
            record_refresh_state(db, DEFAULT_REFRESH_NAME, overall_status, pipeline_details)
            db.commit()

        return {
            "status": overall_status,
            "started_at": started_at,
            "finished_at": now_iso(),
            "jobs": job_summaries,
        }
    except Exception as exc:
        print(f"Refresh cycle error: {exc}")
        return {
            "status": "error",
            "started_at": started_at,
            "finished_at": now_iso(),
            "error": str(exc),
            "jobs": job_summaries,
        }
    finally:
        if lock_acquired:
            try:
                _refresh_lock.release()
                _lock_acquired_at = None
            except Exception as e:
                print(f"Error releasing lock: {e}")


def _refresh_loop():
    # Initial delay so we don't hog the GIL and cause lag during app startup.
    time.sleep(15)
    while True:
        summary = run_refresh_cycle(acquire_lock=True)
        if summary.get("status") == "busy":
            print("Refresh scheduler: refresh already running; skipping this interval.")
        else:
            print(f"Refresh cycle summary: {summary}")
        time.sleep(max(60, REFRESH_INTERVAL_SECONDS))


def start_refresh_scheduler() -> Optional[threading.Thread]:
    global _scheduler_started
    if not ENABLE_REFRESH_SCHEDULER:
        print("Refresh scheduler is disabled.")
        return None

    if _scheduler_started:
        return None

    _scheduler_started = True
    thread = threading.Thread(target=_refresh_loop, name="market-pulse-refresh", daemon=True)
    thread.start()
    print(f"Refresh scheduler started with interval {REFRESH_INTERVAL_SECONDS} seconds.")
    return thread
