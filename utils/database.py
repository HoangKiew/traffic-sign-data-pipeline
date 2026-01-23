from minio import Minio
from pymongo import MongoClient
from pymongo.errors import BulkWriteError, ConnectionFailure
import io
import os
import time
from functools import wraps
from typing import List, Dict, Any, Optional
from config.config import (
    MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY,
    MINIO_BUCKET_RAW, MINIO_SECURE, MONGODB_URI, MONGODB_DB_NAME
)

try:
    from config.optimization_config import (
        MAX_RETRIES, RETRY_DELAY, CONNECTION_TIMEOUT,
        MINIO_POOL_SIZE, MONGODB_POOL_SIZE
    )
except ImportError:
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    CONNECTION_TIMEOUT = 10
    MINIO_POOL_SIZE = 10
    MONGODB_POOL_SIZE = 10

try:
    from utils.logger import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """Decorator to retry failed operations with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts: {e}")
            raise last_exception
        return wrapper
    return decorator


class MinIOClient:
    """Optimized MinIO client with connection pooling and retry logic"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        endpoint = MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
        
        try:
            self.client = Minio(
                endpoint,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE
            )
            self._ensure_buckets()
            logger.info(f"[OK] MinIO connected: {endpoint}")
        except Exception as e:
            logger.error(f"❌ MinIO connection failed: {e}", exc_info=True)
            raise

    def _ensure_buckets(self):
        """Ensure required buckets exist"""
        try:
            if not self.client.bucket_exists(MINIO_BUCKET_RAW):
                self.client.make_bucket(MINIO_BUCKET_RAW)
                logger.info(f"Created bucket: {MINIO_BUCKET_RAW}")
        except Exception as e:
            logger.warning(f"Bucket check/creation warning: {e}")

    @retry_on_failure(max_retries=3)
    def upload_image(self, name: str, data: bytes, bucket: str = MINIO_BUCKET_RAW) -> bool:
        """Upload image with retry logic"""
        try:
            self.client.put_object(
                bucket, name, io.BytesIO(data), len(data), 
                content_type="image/jpeg"
            )
            return True
        except Exception as e:
            logger.debug(f"Upload failed for {name}: {e}")
            raise

    def upload_images_batch(self, images: List[tuple], bucket: str = MINIO_BUCKET_RAW) -> Dict[str, bool]:
        """
        Batch upload images
        Args:
            images: List of (name, data) tuples
        Returns:
            Dict mapping name to success status
        """
        results = {}
        for name, data in images:
            try:
                results[name] = self.upload_image(name, data, bucket)
            except Exception as e:
                logger.error(f"Batch upload failed for {name}: {e}")
                results[name] = False
        return results

    @retry_on_failure(max_retries=3)
    def download_image(self, name: str, bucket: str = MINIO_BUCKET_RAW) -> Optional[bytes]:
        """Download image with retry logic"""
        try:
            response = self.client.get_object(bucket, name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            logger.debug(f"Download failed for {name}: {e}")
            return None

    def list_images(self, bucket: str = MINIO_BUCKET_RAW, prefix: str = "") -> List[str]:
        """List images in bucket"""
        try:
            objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except Exception as e:
            logger.error(f"List images failed: {e}")
            return []
    
    def delete_image(self, name: str, bucket: str = MINIO_BUCKET_RAW) -> bool:
        """Delete image from bucket"""
        try:
            self.client.remove_object(bucket, name)
            return True
        except Exception as e:
            logger.error(f"Delete failed for {name}: {e}")
            return False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass  # Connection pooling handles cleanup


class MongoDBClient:
    """Optimized MongoDB client with connection pooling and batch operations"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        
        try:
            self.client = MongoClient(
                MONGODB_URI,
                maxPoolSize=MONGODB_POOL_SIZE,
                serverSelectionTimeoutMS=CONNECTION_TIMEOUT * 1000,
                connectTimeoutMS=CONNECTION_TIMEOUT * 1000
            )
            self.db = self.client[MONGODB_DB_NAME]
            # Test connection
            self.client.server_info()
            logger.info(f"[OK] MongoDB connected: {MONGODB_DB_NAME}")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}", exc_info=True)
            raise

    @retry_on_failure(max_retries=3)
    def insert_metadata(self, collection: str, data: Dict[str, Any]) -> bool:
        """Insert single document with retry"""
        try:
            self.db[collection].insert_one(data)
            return True
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            raise
    
    def insert_many_metadata(self, collection: str, data_list: List[Dict[str, Any]]) -> int:
        """
        Batch insert documents
        Returns: Number of successfully inserted documents
        """
        if not data_list:
            return 0
            
        try:
            result = self.db[collection].insert_many(data_list, ordered=False)
            return len(result.inserted_ids)
        except BulkWriteError as e:
            # Some documents inserted successfully
            inserted = e.details.get('nInserted', 0)
            logger.warning(f"Partial batch insert: {inserted}/{len(data_list)} succeeded")
            return inserted
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            return 0
    
    def update_metadata(self, collection: str, query: Dict, update: Dict) -> bool:
        """Update document"""
        try:
            result = self.db[collection].update_one(query, {"$set": update})
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False
    
    def find_metadata(self, collection: str, query: Dict = None) -> List[Dict]:
        """Find documents"""
        try:
            cursor = self.db[collection].find(query or {})
            return list(cursor)
        except Exception as e:
            logger.error(f"Find failed: {e}")
            return []
    
    def count_documents(self, collection: str, query: Dict = None) -> int:
        """Count documents"""
        try:
            return self.db[collection].count_documents(query or {})
        except Exception as e:
            logger.error(f"Count failed: {e}")
            return 0
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass  # Connection pooling handles cleanup