import json
import logging
import os
import threading
import time
from collections import deque
from typing import Any, Deque, Dict, Optional


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id
        return json.dumps(payload)


def configure_logging() -> None:
    if os.getenv("MARKET_PULSE_JSON_LOGS", "1") != "1":
        return

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(level=logging.INFO)

    for handler in root_logger.handlers:
        handler.setFormatter(JsonFormatter())


class RequestMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.total_requests = 0
        self.status_counts: Dict[str, int] = {}
        self.latencies_ms: Deque[float] = deque(maxlen=500)

    def record(self, status_code: int, latency_ms: float) -> None:
        status_bucket = f"{status_code // 100}xx"
        with self._lock:
            self.total_requests += 1
            self.status_counts[status_bucket] = self.status_counts.get(status_bucket, 0) + 1
            self.latencies_ms.append(latency_ms)

        # --- Alerting thresholds ---
        # Emit WARNING log lines that external systems (CloudWatch, Datadog, etc.) can alert on.
        if status_code >= 500:
            total = self.total_requests
            errors = self.status_counts.get("5xx", 0)
            if total >= 20 and errors / total > 0.05:
                logging.getLogger("market_pulse.alerts").warning(
                    json.dumps({
                        "type": "ALERT",
                        "metric": "5xx_rate_high",
                        "rate": round(errors / total, 3),
                        "threshold": 0.05,
                    })
                )
        if latency_ms > 2000:
            logging.getLogger("market_pulse.alerts").warning(
                json.dumps({
                    "type": "ALERT",
                    "metric": "high_latency",
                    "latency_ms": round(latency_ms, 1),
                    "threshold_ms": 2000,
                })
            )

    def snapshot(self) -> Dict[str, float]:
        with self._lock:
            avg_latency = (
                sum(self.latencies_ms) / len(self.latencies_ms)
                if self.latencies_ms
                else 0.0
            )
            p95_latency = 0.0
            if self.latencies_ms:
                sorted_latencies = sorted(self.latencies_ms)
                idx = int(0.95 * (len(sorted_latencies) - 1))
                p95_latency = sorted_latencies[idx]
            return {
                "total_requests": float(self.total_requests),
                "avg_latency_ms": round(avg_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "status_2xx": float(self.status_counts.get("2xx", 0)),
                "status_4xx": float(self.status_counts.get("4xx", 0)),
                "status_5xx": float(self.status_counts.get("5xx", 0)),
                "timestamp": time.time(),
            }


request_metrics = RequestMetrics()


_audit_logger = logging.getLogger("market_pulse.audit")


def audit_log(
    event: str,
    user_id: Optional[Any] = None,
    detail: Optional[str] = None,
    ip: Optional[str] = None,
) -> None:
    """Emit a structured AUDIT log line for auth and admin events."""
    payload: Dict[str, Any] = {"type": "AUDIT", "event": event}
    if user_id is not None:
        payload["user_id"] = str(user_id)
    if detail:
        payload["detail"] = detail
    if ip:
        payload["ip"] = ip
    # Emit as WARNING so it survives most log-level filters and is easy to alert on.
    _audit_logger.warning(json.dumps(payload))
