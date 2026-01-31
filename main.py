"""
Optimized Data Cleaning Pipeline
- Raw images: Store ONLY on MinIO
- Processed images: Process in-memory, save to MinIO
- Local storage: Only for temporary processing
"""
import os
import cv2
import numpy as np
import hashlib
from tqdm import tqdm

try:
    from utils.database import MinIOClient
    from processing_labeling.detector import TrafficSignDetector
    from preprocessing.image_processor import ImagePreprocessor
    from utils.logger import get_logger
    from config.optimization_config import IMAGE_PROCESSING_BATCH_SIZE
    logger = get_logger()
except ImportError:
    from utils.database import MinIOClient
    from processing_labeling.detector import TrafficSignDetector
    from preprocessing.image_processor import ImagePreprocessor
    import logging
    logger = logging.getLogger(__name__)
    IMAGE_PROCESSING_BATCH_SIZE = 32

# --- CONFIGURATION ---
MIN_SIZE_KB = 10  # Remove images < 10KB
CONF_FILTER = 0.3  # YOLO threshold for filtering
PROCESSED_BUCKET = "traffic-signs-processed"  # MinIO bucket for processed images


class DataCleaningPipeline:
    """
    Optimized pipeline that stores raw images ONLY on MinIO
    Processes in-memory without saving to local disk
    """
    
    def __init__(self, save_processed_to_minio=True):
        logger.section("Data Cleaning Pipeline")
        logger.info("Initializing...")
        
        self.minio = MinIOClient()
        self.detector = TrafficSignDetector()
        self.preprocessor = ImagePreprocessor()
        self.hashes = set()
        self.save_processed_to_minio = save_processed_to_minio
        
        # Ensure processed bucket exists
        if save_processed_to_minio:
            self._ensure_processed_bucket()
        
        logger.info("Pipeline ready")
    
    def _ensure_processed_bucket(self):
        """Create processed images bucket if not exists"""
        try:
            if not self.minio.client.bucket_exists(PROCESSED_BUCKET):
                self.minio.client.make_bucket(PROCESSED_BUCKET)
                logger.info(f"Created bucket: {PROCESSED_BUCKET}")
        except Exception as e:
            logger.warning(f"Bucket check failed: {e}")
    
    def _get_hash(self, image_bytes):
        """Calculate MD5 hash for deduplication"""
        return hashlib.md5(image_bytes).hexdigest()
    
    def run(self):
        """
        Main pipeline execution
        - Downloads raw images from MinIO
        - Processes in-memory
        - Saves processed images back to MinIO (optional)
        - Does NOT save to local disk
        """
        # Get all raw images from MinIO
        all_images = self.minio.list_images()
        logger.info(f"Found {len(all_images)} raw images on MinIO")
        
        if not all_images:
            logger.warning("No images found in MinIO. Run download_from_web.py first.")
            return
        
        stats = {
            'processed': 0,
            'deleted_small': 0,
            'deleted_duplicate': 0,
            'deleted_no_sign': 0,
            'errors': 0
        }
        
        logger.info("Starting processing...")
        
        for img_name in tqdm(all_images, desc="Processing"):
            try:
                # 1. Download raw image from MinIO
                data = self.minio.download_image(img_name)
                if not data:
                    stats['errors'] += 1
                    continue
                
                # --- FILTER: File size ---
                if len(data) / 1024 < MIN_SIZE_KB:
                    stats['deleted_small'] += 1
                    # Optionally delete from MinIO
                    # self.minio.delete_image(img_name)
                    continue
                
                # --- FILTER: Duplicates ---
                img_hash = self._get_hash(data)
                if img_hash in self.hashes:
                    stats['deleted_duplicate'] += 1
                    # Optionally delete from MinIO
                    # self.minio.delete_image(img_name)
                    continue
                self.hashes.add(img_hash)
                
                # 2. Decode image (in-memory)
                nparr = np.frombuffer(data, np.uint8)
                raw_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if raw_img is None:
                    stats['errors'] += 1
                    continue
                
                # 3. Preprocess (in-memory)
                processed_img, info = self.preprocessor.process_image(
                    raw_img, 
                    check_sharpness=True
                )
                
                # 4. Detect traffic signs (filter out images without signs)
                detections = self.detector.detect(processed_img)
                valid_signs = [d for d in detections if d['confidence'] > CONF_FILTER]

                if not valid_signs:
                    stats['deleted_no_sign'] += 1
                    # KHÔNG xóa ảnh ở raw, chỉ không upload sang processed
                    continue
                
                # 5. Save processed image to MinIO (optional)
                if self.save_processed_to_minio:
                    # Encode processed image
                    _, encoded = cv2.imencode('.jpg', processed_img)
                    processed_data = encoded.tobytes()
                    
                    # Upload to processed bucket
                    processed_name = f"processed_{img_name}"
                    self.minio.upload_image(
                        processed_name, 
                        processed_data, 
                        bucket=PROCESSED_BUCKET
                    )
                
                stats['processed'] += 1
                
            except Exception as e:
                logger.debug(f"Error processing {img_name}: {e}")
                stats['errors'] += 1
                continue
        
        # Print summary
        self._print_summary(stats)
    
    def _print_summary(self, stats):
        """Print processing summary"""
        logger.section("Data Cleaning Summary")
        logger.info(f"Processed successfully: {stats['processed']}")
        logger.info(f"Deleted (too small):   {stats['deleted_small']}")
        logger.info(f"Deleted (duplicate):   {stats['deleted_duplicate']}")
        logger.info(f"Deleted (no sign):     {stats['deleted_no_sign']}")
        logger.info(f"Errors:                {stats['errors']}")
        
        total_deleted = (stats['deleted_small'] + stats['deleted_duplicate'] + 
                        stats['deleted_no_sign'])
        total_processed = stats['processed'] + total_deleted + stats['errors']
        
        if total_processed > 0:
            success_rate = (stats['processed'] / total_processed) * 100
            logger.info(f"Success rate: {success_rate:.1f}%")
        
        logger.info("")
        logger.info("Storage strategy:")
        logger.info("  - Raw images: MinIO only (no local copy)")
        logger.info(f"  - Processed images: MinIO bucket '{PROCESSED_BUCKET}'")
        logger.info("  - Local disk: Clean (no files saved)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Cleaning Pipeline")
    parser.add_argument(
        "--no-save-processed", 
        action="store_true",
        help="Don't save processed images to MinIO (just filter)"
    )
    # Xóa flag --delete-no-sign vì không còn dùng
    args = parser.parse_args()
    
    pipeline = DataCleaningPipeline(
        save_processed_to_minio=not args.no_save_processed
    )
    pipeline.run()