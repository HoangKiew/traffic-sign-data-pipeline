"""
Unified logging system for the traffic sign pipeline
Provides structured logging with file and console output
"""
import logging
import sys
import io
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional


# ────────────────────────────────────────────────────────────────
#     FORCE UTF-8 CHO CONSOLE TRÊN WINDOWS (FIX UnicodeEncodeError)
# ────────────────────────────────────────────────────────────────
if sys.platform.startswith("win"):
    # Cách 1: Re-encode stdout/stderr với UTF-8 + errors='replace' (an toàn nhất)
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.detach(),
            encoding='utf-8',
            errors='replace',           # thay ký tự xấu bằng ?
            line_buffering=True
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.detach(),
            encoding='utf-8',
            errors='replace',
            line_buffering=True
        )
    except (AttributeError, io.UnsupportedOperation):
        # Nếu detach() không hoạt động (hiếm), fallback sang cách khác
        pass

    # Cách 2: Set PYTHONIOENCODING (nếu chạy qua subprocess hoặc cần toàn cục)
    # Nhưng cách trên thường đủ rồi

# ────────────────────────────────────────────────────────────────
#                     PIPELINE LOGGER
# ────────────────────────────────────────────────────────────────

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
        
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler (DEBUG and above) with rotation
        log_file = self.log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'          # Đảm bảo file log hỗ trợ UTF-8
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
        return self.logger
    
    def _replace_unicode(self, msg: str) -> str:
        # Giữ lại để thay emoji nếu muốn, nhưng giờ không cần cho tiếng Việt nữa
        return (
            msg.replace("✅", "OK")
               .replace("⚠️", "WARNING")
               .replace("→", "->")
               .replace("✓", "OK")
               .replace("✗", "X")
               # ... giữ nguyên các thay thế khác nếu bạn thích
        )

    def info(self, msg: str):
        self.logger.info(self._replace_unicode(msg))
    
    def debug(self, msg: str):
        self.logger.debug(self._replace_unicode(msg))
    
    def warning(self, msg: str):
        self.logger.warning(self._replace_unicode(msg))
    
    def error(self, msg: str, exc_info: bool = False):
        self.logger.error(self._replace_unicode(msg), exc_info=exc_info)
    
    def critical(self, msg: str, exc_info: bool = False):
        self.logger.critical(self._replace_unicode(msg), exc_info=exc_info)
    
    def section(self, title: str):
        self.logger.info("  " + self._replace_unicode(title))
    
    def progress(self, current: int, total: int, prefix: str = "Progress"):
        percentage = (current / total * 100) if total > 0 else 0
        self.logger.info(self._replace_unicode(f"{prefix}: {current}/{total} ({percentage:.1f}%)"))


# Global access
def get_logger() -> PipelineLogger:
    return PipelineLogger()