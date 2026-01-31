import os
import cv2
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO
import json
from utils.database import MinIOClient, MongoDBClient

# --- CẤU HÌNH ---
IMG_BUCKET = "traffic-signs-processed"  # Đọc ảnh từ MinIO bucket này
LABEL_DIR = "datasets/labels"     # Thư mục nhãn (Hãy đảm bảo nó TRỐNG)
MODEL_PATH = "yolov8n.pt"         # Model YOLO gốc
MODEL_PATH_X = "yolov8x.pt"       # Model lớn hơn, chính xác hơn
CONF_THRESHOLD = 0.25             # Độ tin cậy để detect
IOU_THRESHOLD = 0.65              # Ngưỡng lọc trùng (thấp hơn = lọc mạnh hơn)
MAX_BOXES = 5                     # Tối đa 5 biển báo/ảnh

# --- DẢI MÀU HSV (V2 - CẢI TIẾN) ---
LOWER_RED1 = np.array([0, 50, 50]); UPPER_RED1 = np.array([15, 255, 255])
LOWER_RED2 = np.array([160, 50, 50]); UPPER_RED2 = np.array([180, 255, 255])
LOWER_BLUE = np.array([90, 50, 50]); UPPER_BLUE = np.array([150, 255, 255])
LOWER_YELLOW = np.array([15, 50, 50]); UPPER_YELLOW = np.array([35, 255, 255])

def get_class_v2(img_crop):
    """Phân loại màu sắc V2"""
    h, w = img_crop.shape[:2]
    area = h * w
    if area == 0: return 4
    
    hsv = cv2.cvtColor(img_crop, cv2.COLOR_BGR2HSV)
    mask_r = cv2.inRange(hsv, LOWER_RED1, UPPER_RED1) + cv2.inRange(hsv, LOWER_RED2, UPPER_RED2)
    mask_b = cv2.inRange(hsv, LOWER_BLUE, UPPER_BLUE)
    mask_y = cv2.inRange(hsv, LOWER_YELLOW, UPPER_YELLOW)
    
    r = cv2.countNonZero(mask_r)
    b = cv2.countNonZero(mask_b)
    y = cv2.countNonZero(mask_y)
    thr = area * 0.05 # 5% diện tích
    
    # Logic ưu tiên
    if y > thr and y > b: return 1 # Nguy hiểm
    if r > thr and r > b: return 1 if (r/area < 0.35) else 0 # 0=Cấm, 1=Nguy hiểm
    if b > thr: return 3 if (b/area > 0.80) else 2 # 2=Hiệu lệnh, 3=Chỉ dẫn
    return 4

def compute_iou(box1, box2):
    """Tính IoU"""
    b1 = box1['xyxy']; b2 = box2['xyxy']
    xi1 = max(b1[0], b2[0]); yi1 = max(b1[1], b2[1])
    xi2 = min(b1[2], b2[2]); yi2 = min(b1[3], b2[3])
    inter = max(0, xi2-xi1) * max(0, yi2-yi1)
    union = box1['area'] + box2['area'] - inter
    return inter/union if union > 0 else 0

def run_master():
    # 1. Khởi tạo
    if not os.path.exists(LABEL_DIR): os.makedirs(LABEL_DIR)
    print("⏳ Đang tải YOLOv8n...")
    model = YOLO(MODEL_PATH)

    # Đọc ảnh từ MinIO thay vì local
    minio = MinIOClient()
    all_images = minio.list_images(bucket=IMG_BUCKET)
    print(f"🚀 BẮT ĐẦU XỬ LÝ TOÀN BỘ {len(all_images)} ẢNH từ MinIO...")

    stats = {0:0, 1:0, 2:0, 3:0, 4:0}
    
    for img_name in tqdm(all_images):
        # Download ảnh từ MinIO
        img_data = minio.download_image(img_name, bucket=IMG_BUCKET)
        if not img_data:
            continue
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None: continue
        h_img, w_img = img.shape[:2]
        
        # 2. Detect bằng YOLO
        results = model(img, verbose=False, conf=CONF_THRESHOLD)
        
        candidates = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Lấy tọa độ
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Crop & Phân loại
                crop = img[y1:y2, x1:x2]
                if crop.size == 0: continue
                
                cls_id = get_class_v2(crop)
                
                # Tính điểm ưu tiên (Diện tích * Hệ số Class)
                # Class 4 bị phạt điểm thấp để dễ bị loại khi lọc trùng
                area = (x2-x1)*(y2-y1)
                score = area * (0.1 if cls_id == 4 else 1.0)
                
                candidates.append({
                    'cls': cls_id,
                    'xyxy': [x1, y1, x2, y2],
                    'area': area,
                    'score': score
                })
        
        # 3. Lọc trùng & Giới hạn số lượng
        # Sort theo điểm cao nhất (Box to + Class xịn lên đầu)
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        final_boxes = []
        while candidates:
            curr = candidates.pop(0)
            is_dup = False
            for kept in final_boxes:
                if compute_iou(curr, kept) > IOU_THRESHOLD:
                    is_dup = True
                    break
            if not is_dup:
                final_boxes.append(curr)
                
        # Giới hạn 5 box/ảnh
        if len(final_boxes) > MAX_BOXES:
            final_boxes = final_boxes[:MAX_BOXES]
            
        # 4. Lưu file .txt
        if final_boxes:
            base_name = os.path.splitext(os.path.basename(img_name))[0]
            txt_path = os.path.join(LABEL_DIR, base_name + ".txt")
            
            with open(txt_path, "w") as f:
                for b in final_boxes:
                    # Convert sang YOLO format (Normalized center)
                    x1, y1, x2, y2 = b['xyxy']
                    xc = ((x1+x2)/2) / w_img
                    yc = ((y1+y2)/2) / h_img
                    w = (x2-x1) / w_img
                    h = (y2-y1) / h_img
                    
                    f.write(f"{b['cls']} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
                    stats[b['cls']] += 1

    print("\n" + "="*50)
    print("✅ HOÀN THÀNH TẤT CẢ TRONG 1 BƯỚC!")
    print("📊 Thống kê cuối cùng:")
    print(f"   0 - Cấm:       {stats[0]}")
    print(f"   1 - Nguy hiểm: {stats[1]}")
    print(f"   2 - Hiệu lệnh: {stats[2]}")
    print(f"   3 - Chỉ dẫn:   {stats[3]}")
    print(f"   4 - Khác:      {stats[4]}")
    print(f"👉 Tổng số vật thể: {sum(stats.values())}")
    print("="*50)

def run_compare_yolo():
    if not os.path.exists(COMPARE_DIR): os.makedirs(COMPARE_DIR)
    img_files = glob.glob(os.path.join(IMG_DIR, "*.*"))
    print(f"🚦 ĐANG SO SÁNH YOLOv8n vs YOLOv8x trên {len(img_files)} ảnh...")

    model_n = YOLO(MODEL_PATH_N)
    model_x = YOLO(MODEL_PATH_X)

    compare_metadata = []

    for img_path in tqdm(img_files):
        img = cv2.imread(img_path)
        if img is None: continue
        h_img, w_img = img.shape[:2]
        base_name = os.path.splitext(os.path.basename(img_path))[0]

        # Detect bằng YOLOv8n
        results_n = model_n(img, verbose=False, conf=CONF_THRESHOLD)
        boxes_n = []
        for r in results_n:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                crop = img[y1:y2, x1:x2]
                cls_id = get_class_v2(crop)
                boxes_n.append({'cls': cls_id, 'xyxy': [x1, y1, x2, y2]})

        # Detect bằng YOLOv8x
        results_x = model_x(img, verbose=False, conf=CONF_THRESHOLD)
        boxes_x = []
        for r in results_x:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                crop = img[y1:y2, x1:x2]
                cls_id = get_class_v2(crop)
                boxes_x.append({'cls': cls_id, 'xyxy': [x1, y1, x2, y2]})

        # Lưu metadata so sánh cho từng ảnh
        compare_metadata.append({
            "image_name": base_name,
            "yolov8n": [{"class_id": b['cls'], "bbox": b['xyxy']} for b in boxes_n],
            "yolov8x": [{"class_id": b['cls'], "bbox": b['xyxy']} for b in boxes_x]
        })

        # Vẽ lên ảnh để so sánh
        img_compare = img.copy()
        img_compare = draw_boxes(img_compare, boxes_n, (0,255,0), "n:")
        img_compare = draw_boxes(img_compare, boxes_x, (0,0,255), "x:")

        # Lưu ảnh so sánh
        cv2.imwrite(os.path.join(COMPARE_DIR, f"{base_name}_compare.jpg"), img_compare)

        # Lưu crop từng biển báo (cả 2 model)
        for idx, b in enumerate(boxes_n):
            x1, y1, x2, y2 = b['xyxy']
            crop = img[y1:y2, x1:x2]
            cv2.imwrite(os.path.join(COMPARE_DIR, f"{base_name}_n_{idx}.jpg"), crop)
        for idx, b in enumerate(boxes_x):
            x1, y1, x2, y2 = b['xyxy']
            crop = img[y1:y2, x1:x2]
            cv2.imwrite(os.path.join(COMPARE_DIR, f"{base_name}_x_{idx}.jpg"), crop)

    # Lưu metadata so sánh ra file JSON
    with open(os.path.join(COMPARE_DIR, "compare_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(compare_metadata, f, indent=2, ensure_ascii=False)

    print(f"✅ Đã lưu ảnh so sánh tại: {COMPARE_DIR}/")
    print(f"✅ Đã lưu metadata so sánh tại: {COMPARE_DIR}/compare_metadata.json")
    print("Ảnh có khung xanh là YOLOv8n, khung đỏ là YOLOv8x.")

def run_dual_yolo_labeling():
    # Tạo 2 thư mục label riêng cho từng model
    LABEL_DIR_N = "datasets/labels_n"
    LABEL_DIR_X = "datasets/labels_x"
    os.makedirs(LABEL_DIR_N, exist_ok=True)
    os.makedirs(LABEL_DIR_X, exist_ok=True)

    minio = MinIOClient()
    all_images = minio.list_images(bucket=IMG_BUCKET)
    print(f"🚀 Đang gán nhãn bằng 2 model YOLO cho {len(all_images)} ảnh...")

    model_n = YOLO(MODEL_PATH)
    model_x = YOLO(MODEL_PATH_X)

    for img_name in tqdm(all_images):
        img_data = minio.download_image(img_name, bucket=IMG_BUCKET)
        if not img_data:
            continue
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None: continue
        h_img, w_img = img.shape[:2]
        base_name = os.path.splitext(os.path.basename(img_name))[0]

        # YOLOv8n
        results_n = model_n(img, verbose=False, conf=CONF_THRESHOLD)
        with open(os.path.join(LABEL_DIR_N, base_name + ".txt"), "w") as f_n:
            for r in results_n:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    crop = img[y1:y2, x1:x2]
                    if crop.size == 0: continue
                    cls_id = get_class_v2(crop)
                    xc = ((x1+x2)/2) / w_img
                    yc = ((y1+y2)/2) / h_img
                    w = (x2-x1) / w_img
                    h = (y2-y1) / h_img
                    f_n.write(f"{cls_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")

        # YOLOv8x
        results_x = model_x(img, verbose=False, conf=CONF_THRESHOLD)
        with open(os.path.join(LABEL_DIR_X, base_name + ".txt"), "w") as f_x:
            for r in results_x:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    crop = img[y1:y2, x1:x2]
                    if crop.size == 0: continue
                    cls_id = get_class_v2(crop)
                    xc = ((x1+x2)/2) / w_img
                    yc = ((y1+y2)/2) / h_img
                    w = (x2-x1) / w_img
                    h = (y2-y1) / h_img
                    f_x.write(f"{cls_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")

    print("✅ Đã gán nhãn bằng 2 model YOLO cho toàn bộ ảnh!")

def run_dual_yolo_metadata():
    """
    Detect với cả 2 model YOLO cho mỗi ảnh, lưu metadata so sánh vào MongoDB và file JSON.
    """
    os.makedirs(COMPARE_DIR, exist_ok=True)
    minio = MinIOClient()
    mongo = MongoDBClient()
    all_images = minio.list_images(bucket=IMG_BUCKET)
    print(f"🚀 Đang detect & lưu metadata so sánh bằng 2 model YOLO cho {len(all_images)} ảnh...")

    model_n = YOLO(MODEL_PATH)
    model_x = YOLO(MODEL_PATH_X)

    compare_metadata = []

    for img_name in tqdm(all_images):
        img_data = minio.download_image(img_name, bucket=IMG_BUCKET)
        if not img_data:
            continue
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None: continue
        h_img, w_img = img.shape[:2]
        base_name = os.path.splitext(os.path.basename(img_name))[0]

        # YOLOv8n
        results_n = model_n(img, verbose=False, conf=CONF_THRESHOLD)
        boxes_n = []
        for r in results_n:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                crop = img[y1:y2, x1:x2]
                if crop.size == 0: continue
                cls_id = get_class_v2(crop)
                conf = float(box.conf[0])
                boxes_n.append({
                    "class_id": cls_id,
                    "bbox_xyxy": [x1, y1, x2, y2],
                    "confidence": conf
                })

        # YOLOv8x
        results_x = model_x(img, verbose=False, conf=CONF_THRESHOLD)
        boxes_x = []
        for r in results_x:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                crop = img[y1:y2, x1:x2]
                if crop.size == 0: continue
                cls_id = get_class_v2(crop)
                conf = float(box.conf[0])
                boxes_x.append({
                    "class_id": cls_id,
                    "bbox_xyxy": [x1, y1, x2, y2],
                    "confidence": conf
                })

        meta = {
            "image_name": img_name,
            "image_size": {"width": w_img, "height": h_img},
            "yolov8n": boxes_n,
            "yolov8x": boxes_x,
            "created_at": str(datetime.now()),
            "pipeline_stage": "dual_yolo_compare"
        }
        compare_metadata.append(meta)
        # Lưu vào MongoDB
        mongo.insert_metadata(COMPARE_METADATA_COLLECTION, meta)

    # Lưu toàn bộ metadata ra file JSON
    with open(os.path.join(COMPARE_DIR, "dual_yolo_compare_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(compare_metadata, f, indent=2, ensure_ascii=False)

    print(f"✅ Đã lưu metadata so sánh vào MongoDB collection '{COMPARE_METADATA_COLLECTION}'")
    print(f"✅ Đã lưu metadata so sánh vào file: {COMPARE_DIR}/dual_yolo_compare_metadata.json")

if __name__ == "__main__":
    # Thêm lựa chọn chạy so sánh
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--compare", action="store_true", help="So sánh YOLOv8n vs YOLOv8x")
    parser.add_argument("--dual-metadata", action="store_true", help="So sánh & lưu metadata 2 model YOLO vào MongoDB/JSON")
    args = parser.parse_args()
    if args.dual_metadata:
        run_dual_yolo_metadata()
    elif args.compare:
        run_compare_yolo()
    else:
        run_master()