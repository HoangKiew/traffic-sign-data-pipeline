import os
import cv2
import sys
import numpy as np  # <--- Thêm dòng này
from tqdm import tqdm
from datetime import datetime
import argparse
import matplotlib.pyplot as plt  # Thêm để vẽ
import matplotlib.patches as patches
import matplotlib
matplotlib.use('Agg')  # <--- Thêm dòng này ngay sau import matplotlib

# Import module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from processing_labeling.detector import TrafficSignDetector
from utils.database import MongoDBClient, MinIOClient

# --- CẤU HÌNH ---
IMG_SOURCE_BUCKET = "traffic-signs-crop-n"  # Đọc ảnh crop từ MinIO bucket này
LABEL_OUTPUT_DIR = "datasets/labels"           # Nơi lưu file .txt
LABEL_OUTPUT_DIR_N = "datasets/labels_n"      # Nơi lưu file nhãn YOLOv8n
LABEL_OUTPUT_DIR_X = "datasets/labels_x"      # Nơi lưu file nhãn YOLOv8x
MONGO_COLLECTION = "dataset_labels_v1"         # Tên collection trong MongoDB
COMPARE_RESULTS_DIR = "compare_results"         # Thư mục lưu ảnh so sánh
os.makedirs(COMPARE_RESULTS_DIR, exist_ok=True)
CROP_BUCKET_N = "traffic-signs-crop-n"
CROP_BUCKET_X = "traffic-signs-crop-x"

def get_shape_name(crop):
    """
    Phân loại hình dáng biển báo: circle, triangle, square, octagon, polygon, other
    """
    if crop is None or crop.size == 0:
        return "unknown"
    img = cv2.resize(crop, (64, 64))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return "unknown"
    cnt = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(cnt)
    if area < 200:
        return "unknown"
    approx = cv2.approxPolyDP(cnt, 0.04*cv2.arcLength(cnt, True), True)
    sides = len(approx)
    if sides >= 8:
        return "octagon" if sides <= 10 else "circle"
    elif sides == 3:
        return "triangle"
    elif sides == 4:
        return "square"
    elif 5 <= sides <= 7:
        return "polygon"
    else:
        return "other"

def get_class_v2(img_crop):
    """
    Phân loại màu sắc V2 (chuẩn YOLO pipeline)
    """
    if img_crop is None or img_crop.size == 0:
        return 4
    h, w = img_crop.shape[:2]
    area = h * w
    if area == 0: return 4
    hsv = cv2.cvtColor(img_crop, cv2.COLOR_BGR2HSV)
    mask_r = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([15, 255, 255])) + \
             cv2.inRange(hsv, np.array([160, 50, 50]), np.array([180, 255, 255]))
    mask_b = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([150, 255, 255]))
    mask_y = cv2.inRange(hsv, np.array([15, 50, 50]), np.array([35, 255, 255]))
    r = cv2.countNonZero(mask_r)
    b = cv2.countNonZero(mask_b)
    y = cv2.countNonZero(mask_y)
    thr = area * 0.05
    if y > thr and y > b: return 1
    if r > thr and r > b: return 1 if (r/area < 0.35) else 0
    if b > thr: return 3 if (b/area > 0.80) else 2
    return 4

def visualize_compare(img, detections_n, detections_x, img_name):
    """
    Vẽ bounding box của YOLOv8n (xanh) và YOLOv8x (đỏ) trên ảnh crop, lưu file để so sánh.
    """
    fig, ax = plt.subplots(1, figsize=(6,6))
    ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    # YOLOv8n: xanh lá
    for det in detections_n:
        x1, y1, x2, y2 = det['bbox']
        rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=2, edgecolor='lime', facecolor='none')
        ax.add_patch(rect)
        ax.text(x1, y1-5, f"n:{det.get('class_id', '')}", color='lime', fontsize=10, weight='bold')
    # YOLOv8x: đỏ
    for det in detections_x:
        x1, y1, x2, y2 = det['bbox']
        rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=2, edgecolor='red', facecolor='none')
        ax.add_patch(rect)
        ax.text(x1, y2+15, f"x:{det.get('class_id', '')}", color='red', fontsize=10, weight='bold')
    ax.axis('off')
    save_path = os.path.join(COMPARE_RESULTS_DIR, f"{os.path.splitext(os.path.basename(img_name))[0]}_compare.png")
    plt.tight_layout()
    plt.savefig(save_path, dpi=120)
    plt.close()
    print(f"🔎 Đã lưu ảnh so sánh: {save_path}")

def visualize_overall_compare(stats_n, stats_x):
    """
    Vẽ bar chart tổng quát so sánh số lượng object giữa YOLOv8n và YOLOv8x.
    """
    labels = ['YOLOv8n', 'YOLOv8x']
    values = [stats_n['objects'], stats_x['objects']]
    colors = ['limegreen', 'red']
    plt.figure(figsize=(6,5))
    bars = plt.bar(labels, values, color=colors)
    plt.ylabel('Số lượng object')
    plt.title('So sánh tổng số object giữa YOLOv8n và YOLOv8x')
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{int(bar.get_height())}', ha='center', va='bottom', fontweight='bold')
    plt.tight_layout()
    save_path = os.path.join(COMPARE_RESULTS_DIR, "overall_compare.png")
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"🔎 Đã lưu biểu đồ tổng quát: {save_path}")

def visualize_class_compare(class_counts_n, class_counts_x, class_names=None):
    """
    Vẽ bar chart so sánh số lượng object theo từng class giữa YOLOv8n và YOLOv8x.
    """
    import numpy as np
    labels = class_names if class_names else [str(i) for i in range(len(class_counts_n))]
    x = np.arange(len(labels))
    width = 0.35

    plt.figure(figsize=(8,5))
    plt.bar(x - width/2, class_counts_n, width, label='YOLOv8n', color='limegreen')
    plt.bar(x + width/2, class_counts_x, width, label='YOLOv8x', color='red')
    plt.xticks(x, labels)
    plt.ylabel('Số lượng object')
    plt.title('So sánh số lượng object theo class giữa YOLOv8n và YOLOv8x')
    plt.legend()
    for i, v in enumerate(class_counts_n):
        plt.text(i - width/2, v, str(v), ha='center', va='bottom', fontweight='bold', fontsize=10)
    for i, v in enumerate(class_counts_x):
        plt.text(i + width/2, v, str(v), ha='center', va='bottom', fontweight='bold', fontsize=10)
    plt.tight_layout()
    save_path = os.path.join(COMPARE_RESULTS_DIR, "class_compare.png")
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"🔎 Đã lưu biểu đồ so sánh theo class: {save_path}")

def visualize_difference_chart(diff_count, same_count):
    """
    Vẽ biểu đồ so sánh số lượng ảnh có kết quả gán nhãn khác nhau/giống nhau giữa YOLOv8n và YOLOv8x.
    """
    labels = ['Khác nhau', 'Giống nhau']
    values = [diff_count, same_count]
    colors = ['orange', 'skyblue']
    plt.figure(figsize=(6,5))
    bars = plt.bar(labels, values, color=colors)
    plt.ylabel('Số lượng ảnh')
    plt.title('So sánh số lượng ảnh gán nhãn khác nhau giữa YOLOv8n và YOLOv8x')
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{int(bar.get_height())}', ha='center', va='bottom', fontweight='bold')
    plt.tight_layout()
    save_path = os.path.join(COMPARE_RESULTS_DIR, "difference_chart.png")
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"🔎 Đã lưu biểu đồ so sánh khác biệt: {save_path}")

class LabelingPipeline:
    def __init__(self, dual_yolo=False):
        print("🏷️ Khởi tạo Pipeline Gán nhãn & Upload DB...")
        self.dual_yolo = dual_yolo
        if dual_yolo:
            self.detector_n = TrafficSignDetector(model_path="yolov8n.pt")
            self.detector_x = TrafficSignDetector(model_path="yolov8x.pt")
            os.makedirs(LABEL_OUTPUT_DIR_N, exist_ok=True)
            os.makedirs(LABEL_OUTPUT_DIR_X, exist_ok=True)
        else:
            self.detector = TrafficSignDetector()
            os.makedirs(LABEL_OUTPUT_DIR, exist_ok=True)
        self.mongo = MongoDBClient()
        self.minio = MinIOClient()

    def run(self):
        all_images = self.minio.list_images(bucket=IMG_SOURCE_BUCKET)
        if not all_images:
            print(f"❌ Không tìm thấy ảnh trong bucket '{IMG_SOURCE_BUCKET}'. Hãy chạy main.py trước!")
            return

        print(f"📂 Đang xử lý {len(all_images)} ảnh từ MinIO bucket '{IMG_SOURCE_BUCKET}'...")

        count_success = 0
        stats_n = {"images": 0, "objects": 0}
        stats_x = {"images": 0, "objects": 0}

        # Thêm biến đếm theo class cho từng model
        class_counts_n = [0, 0, 0, 0, 0]
        class_counts_x = [0, 0, 0, 0, 0]

        # Thêm biến đếm số lượng object trên từng ảnh cho từng model
        per_image_obj_n = []
        per_image_obj_x = []

        for img_name in tqdm(all_images, desc="Labeling & Uploading"):
            img_data = self.minio.download_image(img_name, bucket=IMG_SOURCE_BUCKET)
            if not img_data:
                continue
            try:
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            except Exception:
                continue
            if img is None:
                continue
            h, w = img.shape[:2]

            if self.dual_yolo:
                # --- Chạy song song cả YOLOv8n và YOLOv8x trên cùng 1 ảnh crop ---
                # YOLOv8n
                detections_n = self.detector_n.detect(img)
                base_name = os.path.splitext(os.path.basename(img_name))[0]
                txt_path_n = os.path.join(LABEL_OUTPUT_DIR_N, base_name + ".txt")
                mongo_labels_n = []
                has_valid_obj_n = False
                obj_count_n = 0
                with open(txt_path_n, "w") as f:
                    for idx, det in enumerate(detections_n):
                        x1, y1, x2, y2 = det['bbox']
                        conf = det['confidence']
                        label_name = det.get('label', 'traffic_sign')
                        crop = img[int(y1):int(y2), int(x1):int(x2)]
                        shape = get_shape_name(crop)
                        color_class = get_class_v2(crop)
                        dw = 1.0 / w
                        dh = 1.0 / h
                        x_center = ((x1 + x2) / 2.0) * dw
                        y_center = ((y1 + y2) / 2.0) * dh
                        width = (x2 - x1) * dw
                        height = (y2 - y1) * dh
                        class_id = color_class
                        f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f} # {shape}\n")
                        mongo_labels_n.append({
                            "class_id": class_id,
                            "class_name": label_name,
                            "shape": shape,
                            "bbox_xyxy": [float(x1), float(y1), float(x2), float(y2)],
                            "bbox_yolo": [float(x_center), float(y_center), float(width), float(height)],
                            "confidence": float(conf),
                            "model": "yolov8n",
                            "trained_by": "yolov8n.pt"
                        })
                        has_valid_obj_n = True
                        obj_count_n += 1
                        # --- Lưu crop vào MinIO theo class ---
                        crop_name = f"{base_name}_n_{idx}.jpg"
                        _, encoded = cv2.imencode('.jpg', crop)
                        crop_path = f"class_{class_id}/{crop_name}"
                        self.minio.upload_image(crop_path, encoded.tobytes(), bucket=CROP_BUCKET_N)
                per_image_obj_n.append(obj_count_n)
                if has_valid_obj_n:
                    metadata_n = {
                        "filename": img_name,
                        "filepath_minio": f"{IMG_SOURCE_BUCKET}/{img_name}",
                        "image_size": {"width": w, "height": h},
                        "objects": mongo_labels_n,
                        "object_count": len(mongo_labels_n),
                        "created_at": datetime.now(),
                        "pipeline_stage": "auto_labeling",
                        "model": "yolov8n",
                        "trained_by": "yolov8n.pt"
                    }
                    self.mongo.insert_metadata(MONGO_COLLECTION, metadata_n)
                    count_success += 1
                    stats_n["images"] += 1
                    stats_n["objects"] += len(mongo_labels_n)
                    class_counts_n[class_id] += 1  # <--- Đếm theo class YOLOv8n

                # YOLOv8x
                detections_x = self.detector_x.detect(img)
                txt_path_x = os.path.join(LABEL_OUTPUT_DIR_X, base_name + ".txt")
                mongo_labels_x = []
                has_valid_obj_x = False
                obj_count_x = 0
                with open(txt_path_x, "w") as f:
                    for idx, det in enumerate(detections_x):
                        x1, y1, x2, y2 = det['bbox']
                        conf = det['confidence']
                        label_name = det.get('label', 'traffic_sign')
                        crop = img[int(y1):int(y2), int(x1):int(x2)]
                        shape = get_shape_name(crop)
                        color_class = get_class_v2(crop)
                        dw = 1.0 / w
                        dh = 1.0 / h
                        x_center = ((x1 + x2) / 2.0) * dw
                        y_center = ((y1 + y2) / 2.0) * dh
                        width = (x2 - x1) * dw
                        height = (y2 - y1) * dh
                        class_id = color_class
                        f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f} # {shape}\n")
                        mongo_labels_x.append({
                            "class_id": class_id,
                            "class_name": label_name,
                            "shape": shape,
                            "bbox_xyxy": [float(x1), float(y1), float(x2), float(y2)],
                            "bbox_yolo": [float(x_center), float(y_center), float(width), float(height)],
                            "confidence": float(conf),
                            "model": "yolov8x",
                            "trained_by": "yolov8x.pt"
                        })
                        has_valid_obj_x = True
                        obj_count_x += 1
                        # --- Lưu crop vào MinIO theo class ---
                        crop_name = f"{base_name}_x_{idx}.jpg"
                        _, encoded = cv2.imencode('.jpg', crop)
                        crop_path = f"class_{class_id}/{crop_name}"
                        self.minio.upload_image(crop_path, encoded.tobytes(), bucket=CROP_BUCKET_X)
                per_image_obj_x.append(obj_count_x)
                if has_valid_obj_x:
                    metadata_x = {
                        "filename": img_name,
                        "filepath_minio": f"{IMG_SOURCE_BUCKET}/{img_name}",
                        "image_size": {"width": w, "height": h},
                        "objects": mongo_labels_x,
                        "object_count": len(mongo_labels_x),
                        "created_at": datetime.now(),
                        "pipeline_stage": "auto_labeling",
                        "model": "yolov8x",
                        "trained_by": "yolov8x.pt"
                    }
                    self.mongo.insert_metadata(MONGO_COLLECTION, metadata_x)
                    stats_x["images"] += 1
                    stats_x["objects"] += len(mongo_labels_x)
                    class_counts_x[class_id] += 1  # <--- Đếm theo class YOLOv8x

                # --- Thêm bước trực quan hóa so sánh ---
                # visualize_compare(img, detections_n, detections_x, img_name)  # <-- Bỏ dòng này nếu không muốn lưu từng ảnh

            else:
                # Single YOLO
                detections = self.detector.detect(img)

                if not detections:
                    continue

                base_name = os.path.splitext(os.path.basename(img_name))[0]
                txt_path = os.path.join(LABEL_OUTPUT_DIR, base_name + ".txt")

                mongo_labels = [] # List chứa các object để up lên Mongo
                has_valid_obj = False

                with open(txt_path, "w") as f:
                    for det in detections:
                        x1, y1, x2, y2 = det['bbox']
                        conf = det['confidence']
                        label_name = det.get('label', 'traffic_sign')

                        dw = 1.0 / w
                        dh = 1.0 / h
                        x_center = ((x1 + x2) / 2.0) * dw
                        y_center = ((y1 + y2) / 2.0) * dh
                        width = (x2 - x1) * dw
                        height = (y2 - y1) * dh

                        class_id = 0
                        f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

                        mongo_labels.append({
                            "class_id": class_id,
                            "class_name": label_name,
                            "bbox_xyxy": [float(x1), float(y1), float(x2), float(y2)],
                            "bbox_yolo": [float(x_center), float(y_center), float(width), float(height)],
                            "confidence": float(conf)
                        })
                        has_valid_obj = True

                if has_valid_obj:
                    metadata = {
                        "filename": img_name,
                        "filepath_minio": f"{IMG_SOURCE_BUCKET}/{img_name}",
                        "image_size": {"width": w, "height": h},
                        "objects": mongo_labels,
                        "object_count": len(mongo_labels),
                        "created_at": datetime.now(),
                        "pipeline_stage": "auto_labeling",
                        "model": "yolov8n",  # <--- Thêm trường này (giả định dùng yolov8n.pt)
                        "trained_by": "yolov8n.pt"  # <--- Thêm trường này
                    }
                    self.mongo.insert_metadata(MONGO_COLLECTION, metadata)
                    count_success += 1

        print("\n" + "="*50)
        print("✅ HOÀN THÀNH QUY TRÌNH!")
        if self.dual_yolo:
            print(f"   - YOLOv8n: {stats_n['images']} ảnh, {stats_n['objects']} object")
            print(f"   - YOLOv8x: {stats_x['images']} ảnh, {stats_x['objects']} object")
            print(f"   - File nhãn YOLOv8n lưu tại: '{LABEL_OUTPUT_DIR_N}'")
            print(f"   - File nhãn YOLOv8x lưu tại: '{LABEL_OUTPUT_DIR_X}'")
            print(f"   - Metadata lưu tại Collection: '{MONGO_COLLECTION}'")
            print("-"*30)
            print("🔎 SO SÁNH SỐ LƯỢNG OBJECT GIỮA 2 MODEL:")
            print(f"   YOLOv8n: {stats_n['objects']} object")
            print(f"   YOLOv8x: {stats_x['objects']} object")
            diff = stats_x['objects'] - stats_n['objects']
            if diff > 0:
                print(f"   ➕ YOLOv8x phát hiện nhiều hơn {diff} object")
            elif diff < 0:
                print(f"   ➖ YOLOv8n phát hiện nhiều hơn {-diff} object")
            else:
                print("   = Hai model phát hiện số lượng object bằng nhau")
            # --- Vẽ biểu đồ tổng quát ---
            visualize_overall_compare(stats_n, stats_x)
            # --- Vẽ biểu đồ so sánh theo class ---
            class_names = ["Cấm", "Nguy hiểm", "Hiệu lệnh", "Chỉ dẫn", "Khác"]
            visualize_class_compare(class_counts_n, class_counts_x, class_names)
            # --- Vẽ biểu đồ so sánh số lượng ảnh có kết quả khác nhau/giống nhau ---
            diff_count = sum([n != x for n, x in zip(per_image_obj_n, per_image_obj_x)])
            same_count = sum([n == x for n, x in zip(per_image_obj_n, per_image_obj_x)])
            print(f"🔎 Số lượng ảnh có kết quả gán nhãn khác nhau giữa YOLOv8n và YOLOv8x: {diff_count}")
            print(f"🔎 Số lượng ảnh có kết quả giống nhau: {same_count}")
            visualize_difference_chart(diff_count, same_count)
        else:
            print(f"   - Số ảnh đã dán nhãn & Up MongoDB: {count_success}")
            print(f"   - File nhãn lưu tại: '{LABEL_OUTPUT_DIR}'")
            print(f"   - Metadata lưu tại Collection: '{MONGO_COLLECTION}'")
        print("="*50)

        print("="*50)
        print("📦 OUTPUT CUỐI CÙNG SAU KHI TRAIN/GÁN NHÃN:")
        if self.dual_yolo:
            print(f"   - Nhãn YOLOv8n: {LABEL_OUTPUT_DIR_N}/")
            print(f"   - Nhãn YOLOv8x: {LABEL_OUTPUT_DIR_X}/")
            print(f"   - Metadata MongoDB: Collection '{MONGO_COLLECTION}'")
            print(f"   - Biểu đồ so sánh: {COMPARE_RESULTS_DIR}/ (overall_compare.png, class_compare.png, difference_chart.png)")
        else:
            print(f"   - Nhãn YOLO: {LABEL_OUTPUT_DIR}/")
            print(f"   - Metadata MongoDB: Collection '{MONGO_COLLECTION}'")
        print("="*50)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--single-yolo", action="store_true", help="Chỉ gán nhãn bằng YOLOv8n (không dual)")
    args = parser.parse_args()
    pipeline = LabelingPipeline(dual_yolo=not args.single_yolo)
    pipeline.run()