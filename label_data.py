import os
import cv2
import sys
from tqdm import tqdm
from datetime import datetime

# Import module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from processing_labeling.detector import TrafficSignDetector
from utils.database import MongoDBClient, MinIOClient

# --- CẤU HÌNH ---
IMG_SOURCE_BUCKET = "traffic-signs-processed"  # Đọc ảnh từ MinIO bucket này
LABEL_OUTPUT_DIR = "datasets/labels"           # Nơi lưu file .txt
MONGO_COLLECTION = "dataset_labels_v1"         # Tên collection trong MongoDB

class LabelingPipeline:
    def __init__(self):
        print("🏷️ Khởi tạo Pipeline Gán nhãn & Upload DB...")
        self.detector = TrafficSignDetector()
        self.mongo = MongoDBClient() # Kết nối MongoDB
        self.minio = MinIOClient()   # Kết nối MinIO
        os.makedirs(LABEL_OUTPUT_DIR, exist_ok=True)

    def run(self):
        # 1. Lấy danh sách ảnh từ MinIO bucket processed
        all_images = self.minio.list_images(bucket=IMG_SOURCE_BUCKET)
        if not all_images:
            print(f"❌ Không tìm thấy ảnh trong bucket '{IMG_SOURCE_BUCKET}'. Hãy chạy main.py trước!")
            return

        print(f"📂 Đang xử lý {len(all_images)} ảnh từ MinIO bucket '{IMG_SOURCE_BUCKET}'...")

        count_success = 0

        # 2. Vòng lặp xử lý
        for img_name in tqdm(all_images, desc="Labeling & Uploading"):
            # Download ảnh từ MinIO
            img_data = self.minio.download_image(img_name, bucket=IMG_SOURCE_BUCKET)
            if not img_data:
                continue

            # Đọc ảnh từ bytes
            try:
                import numpy as np
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            except Exception:
                continue
            if img is None:
                continue

            h, w = img.shape[:2]

            # Detect (Lấy tọa độ)
            detections = self.detector.detect(img)

            if not detections:
                continue

            # Chuẩn bị dữ liệu để lưu
            base_name = os.path.splitext(os.path.basename(img_name))[0]
            txt_path = os.path.join(LABEL_OUTPUT_DIR, base_name + ".txt")

            mongo_labels = [] # List chứa các object để up lên Mongo
            has_valid_obj = False

            # Mở file txt để ghi
            with open(txt_path, "w") as f:
                for det in detections:
                    x1, y1, x2, y2 = det['bbox']
                    conf = det['confidence']
                    label_name = det.get('label', 'traffic_sign')

                    # Normalized center_x, center_y, width, height
                    dw = 1.0 / w
                    dh = 1.0 / h
                    x_center = ((x1 + x2) / 2.0) * dw
                    y_center = ((y1 + y2) / 2.0) * dh
                    width = (x2 - x1) * dw
                    height = (y2 - y1) * dh

                    # Phân loại class_id dựa trên label_name nếu có
                    class_id = 0
                    if label_name == "prohibition":
                        class_id = 0
                    elif label_name == "warning":
                        class_id = 1
                    elif label_name == "command":
                        class_id = 2
                    elif label_name == "instruction":
                        class_id = 3
                    elif label_name == "other":
                        class_id = 4

                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

                    mongo_labels.append({
                        "class_id": class_id,
                        "class_name": label_name,
                        "bbox_xyxy": [float(x1), float(y1), float(x2), float(y2)],
                        "bbox_yolo": [float(x_center), float(y_center), float(width), float(height)],
                        "confidence": float(conf)
                    })
                    has_valid_obj = True

            # --- 3. Upload Metadata lên MongoDB ---
            if has_valid_obj:
                metadata = {
                    "filename": img_name,
                    "filepath_minio": f"{IMG_SOURCE_BUCKET}/{img_name}",
                    "image_size": {"width": w, "height": h},
                    "objects": mongo_labels,
                    "object_count": len(mongo_labels),
                    "created_at": datetime.now(),
                    "pipeline_stage": "auto_labeling"
                }
                self.mongo.insert_metadata(MONGO_COLLECTION, metadata)
                count_success += 1

        print("\n" + "="*50)
        print("✅ HOÀN THÀNH QUY TRÌNH!")
        print(f"   - Số ảnh đã dán nhãn & Up MongoDB: {count_success}")
        print(f"   - File nhãn lưu tại: '{LABEL_OUTPUT_DIR}'")
        print(f"   - Metadata lưu tại Collection: '{MONGO_COLLECTION}'")
        print("="*50)

if __name__ == "__main__":
    pipeline = LabelingPipeline()
    pipeline.run()