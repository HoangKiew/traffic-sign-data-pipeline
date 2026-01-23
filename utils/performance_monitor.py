"""
Performance monitoring and tracking utilities
"""
import time
import psutil
import os
from typing import Dict, Any
from contextlib import contextmanager

try:
    from utils.logger import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Track performance metrics during pipeline execution"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
        self.process = psutil.Process(os.getpid())
    
    @contextmanager
    def track(self, operation_name: str):
        """
        Context manager to track operation time and memory
        
        Usage:
            with monitor.track("data_loading"):
                # your code here
                pass
        """
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            self.metrics[operation_name] = {
                'duration_seconds': duration,
                'memory_mb': end_memory,
                'memory_delta_mb': memory_delta
            }
            
            logger.debug(f"{operation_name}: {duration:.2f}s, Memory: {end_memory:.1f}MB ({memory_delta:+.1f}MB)")
    
    def start_operation(self, operation_name: str):
        """Start tracking an operation"""
        self.start_times[operation_name] = time.time()
    
    def end_operation(self, operation_name: str, items_processed: int = 0):
        """End tracking an operation"""
        if operation_name not in self.start_times:
            logger.warning(f"Operation '{operation_name}' was not started")
            return
        
        duration = time.time() - self.start_times[operation_name]
        memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        self.metrics[operation_name] = {
            'duration_seconds': duration,
            'memory_mb': memory,
            'items_processed': items_processed
        }
        
        if items_processed > 0:
            throughput = items_processed / duration
            logger.info(f"✅ {operation_name}: {duration:.1f}s, {items_processed} items ({throughput:.1f} items/s)")
        else:
            logger.info(f"✅ {operation_name}: {duration:.1f}s")
        
        del self.start_times[operation_name]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        return self.metrics
    
    def print_summary(self):
        """Print performance summary"""
        logger.section("Performance Summary")
        
        total_time = sum(m.get('duration_seconds', 0) for m in self.metrics.values())
        max_memory = max((m.get('memory_mb', 0) for m in self.metrics.values()), default=0)
        
        logger.info(f"Total execution time: {total_time:.1f}s ({total_time/60:.1f}min)")
        logger.info(f"Peak memory usage: {max_memory:.1f}MB")
        logger.info("")
        logger.info("Operation breakdown:")
        
        for op_name, metrics in self.metrics.items():
            duration = metrics.get('duration_seconds', 0)
            items = metrics.get('items_processed', 0)
            
            if items > 0:
                throughput = items / duration if duration > 0 else 0
                logger.info(f"  • {op_name}: {duration:.1f}s ({items} items, {throughput:.1f} items/s)")
            else:
                logger.info(f"  • {op_name}: {duration:.1f}s")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get current system information"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_available_mb': psutil.virtual_memory().available / 1024 / 1024,
            'disk_usage_percent': psutil.disk_usage('/').percent
        }


# Global monitor instance
_monitor = None

def get_monitor() -> PerformanceMonitor:
    """Get global performance monitor"""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor
