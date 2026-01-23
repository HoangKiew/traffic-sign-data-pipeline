"""
Performance optimization configuration
Centralized settings for batch sizes, threading, and resource limits
"""
import os
from multiprocessing import cpu_count

# ============================================================================
# BATCH PROCESSING
# ============================================================================
YOLO_BATCH_SIZE = 16  # Number of images to process in one YOLO inference
IMAGE_PROCESSING_BATCH_SIZE = 32  # Batch size for preprocessing
DATABASE_BATCH_SIZE = 100  # Batch insert/upload size

# ============================================================================
# PARALLELIZATION
# ============================================================================
# CPU-bound tasks (image processing, classification)
NUM_WORKERS = min(cpu_count() - 1, 8)  # Leave 1 core for system

# I/O-bound tasks (MinIO, MongoDB, web scraping)
THREAD_POOL_SIZE = 16  # Increased from 8
MAX_CONCURRENT_DOWNLOADS = 10  # Concurrent web downloads

# ============================================================================
# MEMORY MANAGEMENT
# ============================================================================
MAX_IMAGES_IN_MEMORY = 1000  # Maximum images to hold in memory
CACHE_SIZE_MB = 512  # Image cache size in MB
ENABLE_STREAMING = True  # Stream large datasets instead of loading all

# ============================================================================
# RETRY & ERROR HANDLING
# ============================================================================
MAX_RETRIES = 3  # Maximum retry attempts for failed operations
RETRY_DELAY = 2  # Initial delay in seconds (exponential backoff)
TIMEOUT_SECONDS = 30  # Timeout for network operations

# ============================================================================
# CHECKPOINT & RESUME
# ============================================================================
ENABLE_CHECKPOINTS = True  # Save progress periodically
CHECKPOINT_INTERVAL = 100  # Save checkpoint every N images
CHECKPOINT_DIR = "checkpoints"

# ============================================================================
# CONNECTION POOLING
# ============================================================================
MINIO_POOL_SIZE = 10  # MinIO connection pool size
MONGODB_POOL_SIZE = 10  # MongoDB connection pool size
CONNECTION_TIMEOUT = 10  # Connection timeout in seconds

# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================
ENABLE_PERFORMANCE_TRACKING = True  # Track execution times
LOG_MEMORY_USAGE = True  # Log memory consumption
REPORT_INTERVAL = 50  # Report progress every N items

# ============================================================================
# WEB SCRAPING
# ============================================================================
SCRAPER_RATE_LIMIT = 0.5  # Delay between requests (seconds)
SCRAPER_MAX_IMAGES_PER_KEYWORD = 200  # Reduced from 300 to avoid bans
SCRAPER_TIMEOUT = 15  # Timeout for image downloads
SCRAPER_SKIP_ON_ERROR = True  # Continue on individual failures

# ============================================================================
# YOLO OPTIMIZATION
# ============================================================================
YOLO_WARMUP_ITERATIONS = 3  # Warmup runs before actual inference
YOLO_HALF_PRECISION = False  # Use FP16 (requires GPU)
YOLO_DEVICE = "cuda" if os.getenv("CUDA_VISIBLE_DEVICES") else "cpu"

# ============================================================================
# VALIDATION
# ============================================================================
VALIDATE_BEFORE_PROCESSING = True  # Check data integrity before processing
MIN_VALID_IMAGES_THRESHOLD = 10  # Minimum images required to proceed
