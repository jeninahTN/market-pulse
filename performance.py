"""
Performance monitoring and optimization utilities.
Includes bounded metrics storage to prevent memory growth.
"""

import time
import psutil
import os
from functools import wraps
from typing import Dict, Any, List
from collections import OrderedDict
from app.cache import get_cache_stats


class PerformanceMonitor:
    """Monitor application performance with bounded metric storage."""
    
    def __init__(self, max_metrics_per_function: int = 100):
        self.metrics: Dict[str, List] = {}
        self.start_time = time.time()
        self.max_metrics_per_function = max_metrics_per_function
    
    def track_function(self, func_name: str):
        """Decorator to track function performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    status = "success"
                except Exception as e:
                    result = None
                    status = f"error: {str(e)}"
                
                duration = time.time() - start
                
                # Store metrics with bounded size
                if func_name not in self.metrics:
                    self.metrics[func_name] = []
                
                self.metrics[func_name].append({
                    'duration': duration,
                    'status': status,
                    'timestamp': time.time()
                })
                
                # Keep only last N calls per function (bounded)
                if len(self.metrics[func_name]) > self.max_metrics_per_function:
                    self.metrics[func_name] = self.metrics[func_name][-self.max_metrics_per_function:]
                
                return result
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}
        
        for func_name, calls in self.metrics.items():
            if not calls:
                continue
                
            durations = [call['duration'] for call in calls]
            successful_calls = [call for call in calls if call['status'] == 'success']
            
            stats[func_name] = {
                'total_calls': len(calls),
                'successful_calls': len(successful_calls),
                'avg_duration': sum(durations) / len(durations) if durations else 0,
                'min_duration': min(durations) if durations else 0,
                'max_duration': max(durations) if durations else 0,
                'last_call': calls[-1]['duration'] if calls else 0,
                'success_rate': len(successful_calls) / len(calls) * 100 if calls else 0
            }
        
        return stats
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system resource statistics"""
        process = psutil.Process(os.getpid())
        
        return {
            'uptime_seconds': time.time() - self.start_time,
            'cpu_percent': psutil.cpu_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'memory_percent': process.memory_percent(),
            'thread_count': process.num_threads(),
            'cache_stats': get_cache_stats()
        }


# Global performance monitor
performance_monitor = PerformanceMonitor()


def track_performance(func_name: str):
    """Decorator to track performance"""
    return performance_monitor.track_function(func_name)
