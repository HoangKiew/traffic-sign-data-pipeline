"""
Unified logging system for the traffic sign pipeline
Provides structured logging with file and console output
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional


class PipelineLogger:
    """Centralized logger for the entire pipeline"""
    
    _instance: Optional['PipelineLogger'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger("TrafficSignPipeline")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()
        
        # Console handler (INFO and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Fix Unicode encoding for Windows
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Force UTF-8 encoding on Windows
        if hasattr(console_handler.stream, 'reconfigure'):
            try:
                console_handler.stream.reconfigure(encoding='utf-8')
            except:
                pass
        
        # File handler (DEBUG and above) with rotation
        log_file = self.log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        self.logger.info("="*60)
        self.logger.info("Pipeline Logger Initialized")
        self.logger.info(f"Log file: {log_file}")
        self.logger.info("="*60)
    
    def get_logger(self) -> logging.Logger:
        """Get the logger instance"""
        return self.logger
    
    def info(self, msg: str):
        """Log info message"""
        self.logger.info(msg)
    
    def debug(self, msg: str):
        """Log debug message"""
        self.logger.debug(msg)
    
    def warning(self, msg: str):
        """Log warning message"""
        self.logger.warning(msg)
    
    def error(self, msg: str, exc_info: bool = False):
        """Log error message"""
        self.logger.error(msg, exc_info=exc_info)
    
    def critical(self, msg: str, exc_info: bool = False):
        """Log critical message"""
        self.logger.critical(msg, exc_info=exc_info)
    
    def section(self, title: str):
        """Log a section header"""
        self.logger.info("")
        self.logger.info("="*60)
        self.logger.info(f"  {title}")
        self.logger.info("="*60)
    
    def progress(self, current: int, total: int, prefix: str = "Progress"):
        """Log progress"""
        percentage = (current / total * 100) if total > 0 else 0
        self.logger.info(f"{prefix}: {current}/{total} ({percentage:.1f}%)")


# Global logger instance
def get_logger() -> PipelineLogger:
    """Get the global logger instance"""
    return PipelineLogger()
