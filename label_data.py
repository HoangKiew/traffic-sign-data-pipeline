import os
import cv2
import sys
from tqdm import tqdm
from datetime import datetime

# Import module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from processing_labeling.detector import TrafficSignDetector
from utils.database import MongoDBClient

# --- CẤU HÌNH ---
IMG_SOURCE_DIR = "datasets/images"       # Nơi đọc ảnh sạch
LABEL_OUTPUT_DIR = "datasets/labels"     # Nơi lưu file .txt
MONGO_COLLECTION = "dataset_labels_v1"   # Tên collection trong MongoDB

class LabelingPipeline:
    def __init__(self):
        print("🏷️ Khởi tạo Pipeline Gán nhãn & Upload DB...")
        self.detector = TrafficSignDetector()
        self.mongo = MongoDBClient() # Kết nối MongoDB
        os.makedirs(LABEL_OUTPUT_DIR, exist_ok=True)

    def run(self):
        # 1. Kiểm tra thư mục ảnh
        if not os.path.exists(IMG_SOURCE_DIR):
            print(f"❌ Không thấy thư mục '{IMG_SOURCE_DIR}'. Hãy chạy main.py trước!")
            return

        image_files = [f for f in os.listdir(IMG_SOURCE_DIR) if f.endswith(('.jpg', '.png', '.jpeg'))]
        
        if not image_files:
            print("⚠️ Thư mục ảnh trống!")
            return

        print(f"📂 Đang xử lý {len(image_files)} ảnh...")
        
        count_success = 0

        # 2. Vòng lặp xử lý
        for img_name in tqdm(image_files, desc="Labeling & Uploading"):
            img_path = os.path.join(IMG_SOURCE_DIR, img_name)
            
            # Đọc ảnh
            img = cv2.imread(img_path)
            if img is None: continue
            
            h, w = img.shape[:2]

            # Detect (Lấy tọa độ)
            detections = self.detector.detect(img)
            
            if not detections: continue

            # Chuẩn bị dữ liệu để lưu
            txt_path = os.path.join(LABEL_OUTPUT_DIR, os.path.splitext(img_name)[0] + ".txt")
            
            mongo_labels = [] # List chứa các object để up lên Mongo
            has_valid_obj = False

            # Mở file txt để ghi
            with open(txt_path, "w") as f:
                for det in detections:
                    # Lấy thông tin từ detector
                    # det format: {'bbox': [x1, y1, x2, y2], 'confidence': float, 'label': str}
                    x1, y1, x2, y2 = det['bbox']
                    conf = det['confidence']
                    label_name = det.get('label', 'traffic_sign')
                    
                    # --- 1. Ghi file .txt (Format YOLO) ---
                    # Normalized center_x, center_y, width, height
                    dw = 1.0 / w
                    dh = 1.0 / h
                    x_center = ((x1 + x2) / 2.0) * dw
                    y_center = ((y1 + y2) / 2.0) * dh
                    width = (x2 - x1) * dw
                    height = (y2 - y1) * dh
                    
                    # Giả định class_id = 0
                    class_id = 0
                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                    
                    # --- 2. Chuẩn bị data cho MongoDB ---
                    mongo_labels.append({
                        "class_id": class_id,
                        "class_name": label_name,
                        "bbox_xyxy": [float(x1), float(y1), float(x2), float(y2)], # Tọa độ gốc
                        "bbox_yolo": [float(x_center), float(y_center), float(width), float(height)], # Tọa độ YOLO
                        "confidence": float(conf)
                    })
                    has_valid_obj = True

            # --- 3. Upload Metadata lên MongoDB ---
            if has_valid_obj:
                metadata = {
                    "filename": img_name,
                    "filepath_local": img_path,
                    "image_size": {"width": w, "height": h},
                    "objects": mongo_labels, # List các biển báo trong ảnh
                    "object_count": len(mongo_labels),
                    "created_at": datetime.now(),
                    "pipeline_stage": "auto_labeling"
                }
                
                # Gọi hàm insert của MongoDBClient (từ file database.py)
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