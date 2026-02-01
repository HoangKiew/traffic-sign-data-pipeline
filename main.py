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
from datetime import datetime

try:
    from utils.database import MinIOClient, MongoDBClient
    from processing_labeling.detector import TrafficSignDetector
    from preprocessing.image_processor import ImagePreprocessor
    from utils.logger import get_logger
    from config.optimization_config import IMAGE_PROCESSING_BATCH_SIZE
    logger = get_logger()
except ImportError:
    from utils.database import MinIOClient, MongoDBClient
    from processing_labeling.detector import TrafficSignDetector
    from preprocessing.image_processor import ImagePreprocessor
    import logging
    logger = logging.getLogger(__name__)
    IMAGE_PROCESSING_BATCH_SIZE = 32

# --- CONFIGURATION ---
MIN_SIZE_KB = 10  # Remove images < 10KB
CONF_FILTER = 0.3  # YOLO threshold for filtering
PROCESSED_BUCKET = "traffic-signs-processed"  # MinIO bucket for processed images
CROP_BUCKET_N = "traffic-signs-crop-n"
CROP_BUCKET_X = "traffic-signs-crop-x"
METADATA_COLLECTION = "crop_metadata_dual_yolo"

class DataCleaningPipeline:
    """
    Optimized pipeline that stores raw images ONLY on MinIO
    Processes in-memory without saving to local disk
    """
    
    def __init__(self, save_processed_to_minio=True, dual_yolo_classify=False):
        logger.section("Data Cleaning Pipeline")
        logger.info("Initializing...")
        
        self.minio = MinIOClient()
        self.detector_n = TrafficSignDetector(model_path="yolov8n.pt")
        self.detector_x = TrafficSignDetector(model_path="yolov8x.pt") if dual_yolo_classify else None
        self.preprocessor = ImagePreprocessor()
        self.hashes = set()
        self.save_processed_to_minio = save_processed_to_minio
        self.dual_yolo_classify = dual_yolo_classify
        self.crop_bucket_n = CROP_BUCKET_N
        self.crop_bucket_x = CROP_BUCKET_X
        self.mongo = MongoDBClient()
        
        if save_processed_to_minio:
            self._ensure_processed_bucket()
            self._ensure_crop_buckets()
        
        logger.info("Pipeline ready")
    
    def _ensure_processed_bucket(self):
        """Create processed images bucket if not exists"""
        try:
            if not self.minio.client.bucket_exists(PROCESSED_BUCKET):
                self.minio.client.make_bucket(PROCESSED_BUCKET)
                logger.info(f"Created bucket: {PROCESSED_BUCKET}")
        except Exception as e:
            logger.warning(f"Bucket check failed: {e}")
    
    def _ensure_crop_buckets(self):
        """Create crop buckets if not exists"""
        for bucket in [self.crop_bucket_n, self.crop_bucket_x]:
            try:
                if not self.minio.client.bucket_exists(bucket):
                    self.minio.client.make_bucket(bucket)
                    logger.info(f"Created bucket: {bucket}")
            except Exception as e:
                logger.warning(f"Bucket check failed: {e}")
    
    def _get_hash(self, image_bytes):
        """Calculate MD5 hash for deduplication"""
        return hashlib.md5(image_bytes).hexdigest()
    
    def _crop_box(self, img, bbox):
        """
        Cắt ảnh theo bbox [x1, y1, x2, y2], đảm bảo không vượt ngoài biên ảnh.
        """
        x1, y1, x2, y2 = map(int, bbox)
        h, w = img.shape[:2]
        x1 = max(0, min(x1, w-1))
        x2 = max(0, min(x2, w))
        y1 = max(0, min(y1, h-1))
        y2 = max(0, min(y2, h))
        if x2 <= x1 or y2 <= y1:
            # Nếu bbox không hợp lệ, trả về ảnh gốc (hoặc raise)
            return img
        return img[y1:y2, x1:x2]

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
                    logger.debug(f"Lỗi: Không tải được ảnh '{img_name}' từ MinIO.")
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
                    logger.debug(f"Lỗi: Không decode được ảnh '{img_name}'. Có thể file bị hỏng hoặc không phải ảnh.")
                    stats['errors'] += 1
                    continue
                
                # 3. Preprocess (in-memory)
                try:
                    processed_img, info = self.preprocessor.process_image(
                        raw_img, 
                        check_sharpness=True
                    )
                except Exception as e:
                    logger.debug(f"Lỗi: Tiền xử lý thất bại với '{img_name}': {e}")
                    stats['errors'] += 1
                    continue
                
                # 4. Dual YOLO detect, crop, save crop & metadata
                if self.dual_yolo_classify and self.detector_x:
                    detections_n = self.detector_n.detect(processed_img)
                    detections_x = self.detector_x.detect(processed_img)
                    valid_signs_n = [d for d in detections_n if d['confidence'] > CONF_FILTER]
                    valid_signs_x = [d for d in detections_x if d['confidence'] > CONF_FILTER]
                    if not valid_signs_n and not valid_signs_x:
                        stats['deleted_no_sign'] += 1
                        continue

                    # Crop & save for YOLOv8n
                    for idx, det in enumerate(valid_signs_n):
                        crop = self._crop_box(processed_img, det['bbox'])
                        crop_name = f"n_{os.path.splitext(img_name)[0]}_{idx}.jpg"
                        _, encoded = cv2.imencode('.jpg', crop)
                        self.minio.upload_image(
                            crop_name, encoded.tobytes(), bucket=self.crop_bucket_n
                        )
                        # Save metadata
                        meta = {
                            "image_name": img_name,
                            "crop_name": crop_name,
                            "model": "yolov8n",
                            "bbox": [float(x) for x in det['bbox']],
                            "confidence": float(det['confidence']),
                            "label": det.get('label', ''),
                            "created_at": datetime.now(),
                        }
                        self.mongo.insert_metadata(METADATA_COLLECTION, meta)

                    # Crop & save for YOLOv8x
                    for idx, det in enumerate(valid_signs_x):
                        crop = self._crop_box(processed_img, det['bbox'])
                        crop_name = f"x_{os.path.splitext(img_name)[0]}_{idx}.jpg"
                        _, encoded = cv2.imencode('.jpg', crop)
                        self.minio.upload_image(
                            crop_name, encoded.tobytes(), bucket=self.crop_bucket_x
                        )
                        meta = {
                            "image_name": img_name,
                            "crop_name": crop_name,
                            "model": "yolov8x",
                            "bbox": [float(x) for x in det['bbox']],
                            "confidence": float(det['confidence']),
                            "label": det.get('label', ''),
                            "created_at": datetime.now(),
                        }
                        self.mongo.insert_metadata(METADATA_COLLECTION, meta)

                else:
                    detections = self.detector_n.detect(processed_img)
                    valid_signs = [d for d in detections if d['confidence'] > CONF_FILTER]
                    if not valid_signs:
                        stats['deleted_no_sign'] += 1
                        continue
                    # Crop & save for YOLOv8n only
                    for idx, det in enumerate(valid_signs):
                        crop = self._crop_box(processed_img, det['bbox'])
                        crop_name = f"n_{os.path.splitext(img_name)[0]}_{idx}.jpg"
                        _, encoded = cv2.imencode('.jpg', crop)
                        self.minio.upload_image(
                            crop_name, encoded.tobytes(), bucket=self.crop_bucket_n
                        )
                        meta = {
                            "image_name": img_name,
                            "crop_name": crop_name,
                            "model": "yolov8n",
                            "bbox": [float(x) for x in det['bbox']],
                            "confidence": float(det['confidence']),
                            "label": det.get('label', ''),
                            "created_at": datetime.now(),
                        }
                        self.mongo.insert_metadata(METADATA_COLLECTION, meta)

                # Save processed image to MinIO (optional, for visualization)
                if self.save_processed_to_minio:
                    _, encoded = cv2.imencode('.jpg', processed_img)
                    processed_name = f"processed_{img_name}"
                    self.minio.upload_image(
                        processed_name, 
                        encoded.tobytes(), 
                        bucket=PROCESSED_BUCKET
                    )
                stats['processed'] += 1
                
            except Exception as e:
                logger.debug(f"Lỗi không xác định khi xử lý '{img_name}': {e}")
                stats['errors'] += 1
                continue
        
        # Print summary
        self._print_summary(stats)
        # --- Cảnh báo nếu lỗi toàn bộ hoặc tỷ lệ lỗi cao ---
        total_images = len(all_images)
        if stats['errors'] == total_images:
            logger.warning("TẤT CẢ ảnh đều lỗi! Kiểm tra lại dữ liệu ảnh (có thể ảnh bị hỏng hoặc không đúng định dạng).")
        elif stats['errors'] > 0.5 * total_images:
            logger.warning(f"Tỷ lệ lỗi cao: {stats['errors']} trên {total_images} ảnh. Hãy kiểm tra lại pipeline tiền xử lý và định dạng ảnh.")

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
    parser.add_argument(
        "--dual-yolo-classify",
        action="store_true",
        help="Dùng 2 model YOLO để detect & phân loại song song"
    )
    args = parser.parse_args()
    
    pipeline = DataCleaningPipeline(
        save_processed_to_minio=not args.no_save_processed,
        dual_yolo_classify=args.dual_yolo_classify
    )
    pipeline.run()