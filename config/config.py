"""
Cấu hình cho Data Pipeline xử lý biển báo giao thông
"""
import os
from dotenv import load_dotenv

load_dotenv()

# MinIO Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_RAW = os.getenv("MINIO_BUCKET_RAW", "traffic-signs-raw")
MINIO_BUCKET_PROCESSED = os.getenv("MINIO_BUCKET_PROCESSED", "traffic-signs-processed")
MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "traffic_signs_db")
MONGODB_COLLECTION_METADATA = os.getenv("MONGODB_COLLECTION_METADATA", "metadata")
MONGODB_COLLECTION_LABELS = os.getenv("MONGODB_COLLECTION_LABELS", "labels")

# Image Processing Configuration
IMAGE_TARGET_SIZE = (640, 640)  # Kích thước chuẩn
PADDING_COLOR = (128, 128, 128)  # Màu xám cho padding

# Preprocessing Parameters
BILATERAL_D = 9
BILATERAL_SIGMA_COLOR = 75
BILATERAL_SIGMA_SPACE = 75
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID_SIZE = (8, 8)
SHARPNESS_THRESHOLD = 100.0  # Laplacian variance threshold
UNSHARP_AMOUNT = 1.5
UNSHARP_SIGMA = 1.0

# YOLO Configuration
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")  # Sử dụng YOLOv8 nano
YOLO_MODEL_PATH_X = os.getenv("YOLO_MODEL_PATH_X", "yolov8x.pt")  # Sử dụng YOLOv8x (nếu cần)
YOLO_CONFIDENCE_THRESHOLD = 0.5

# VLM Configuration
VLM_MODEL_NAME = os.getenv("VLM_MODEL_NAME", "Salesforce/blip-image-captioning-base")
VLM_DEVICE = os.getenv("VLM_DEVICE", "cpu")  # "cuda" nếu có GPU

# Dataset Split Configuration
TRAIN_TEST_SPLIT_RATIO = 0.8  # 80% train, 20% test
MIN_SAMPLES_PER_CLASS = 10  # Số lượng mẫu tối thiểu mỗi lớp

# Output Directories
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
TRAIN_IMAGES_DIR = os.path.join(OUTPUT_DIR, "train", "images")
TRAIN_LABELS_DIR = os.path.join(OUTPUT_DIR, "train", "labels")
TEST_IMAGES_DIR = os.path.join(OUTPUT_DIR, "test", "images")
TEST_LABELS_DIR = os.path.join(OUTPUT_DIR, "test", "labels")

# Dùng cả 2 bucket crop để train
MINIO_BUCKET_CROP_TRAIN_N = "traffic-signs-crop-n"
MINIO_BUCKET_CROP_TRAIN_X = "traffic-signs-crop-x"

# Create output directories if they don't exist
os.makedirs(TRAIN_IMAGES_DIR, exist_ok=True)
os.makedirs(TEST_IMAGES_DIR, exist_ok=True)
os.makedirs(TRAIN_LABELS_DIR, exist_ok=True)
os.makedirs(TEST_LABELS_DIR, exist_ok=True)

# Tự động tạo bucket MinIO nếu chưa tồn tại
def ensure_minio_buckets():
    try:
        from minio import Minio
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        buckets = [
            MINIO_BUCKET_RAW,
            MINIO_BUCKET_PROCESSED,
            MINIO_BUCKET_CROP_TRAIN_N,
            MINIO_BUCKET_CROP_TRAIN_X
        ]
        for bucket in buckets:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
    except Exception as e:
        print(f"[MinIO] Bucket creation skipped or failed: {e}")

# Gọi hàm này ở đầu pipeline (ví dụ: trong unified_pipeline.py hoặc main.py)
# ensure_minio_buckets()
