import os
import cv2
import glob
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO

# --- CẤU HÌNH ---
IMG_DIR = "datasets/images"       # Thư mục ảnh sạch
LABEL_DIR = "datasets/labels"     # Thư mục nhãn (Hãy đảm bảo nó TRỐNG)
MODEL_PATH = "yolov8n.pt"         # Model YOLO gốc (KHÔNG dùng best.pt ở bước này)
MODEL_PATH_X = "yolov8x.pt"       # Model lớn hơn, chính xác hơn
CONF_THRESHOLD = 0.25             # Độ tin cậy để detect
IOU_THRESHOLD = 0.65              # Ngưỡng lọc trùng (thấp hơn = lọc mạnh hơn)
MAX_BOXES = 5                     # Tối đa 5 biển báo/ảnh

COMPARE_DIR = "compare_results"   # Thư mục lưu kết quả so sánh YOLO

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

def compute_iou(box1, box2):
    """Tính IoU"""
    b1 = box1['xyxy']; b2 = box2['xyxy']
    xi1 = max(b1[0], b2[0]); yi1 = max(b1[1], b2[1])
    xi2 = min(b1[2], b2[2]); yi2 = min(b1[3], b2[3])
    inter = max(0, xi2-xi1) * max(0, yi2-yi1)
    union = box1['area'] + box2['area'] - inter
    return inter/union if union > 0 else 0

LABEL_DIR_N = "datasets/labels_n"   # Nhãn YOLOv8n
LABEL_DIR_X = "datasets/labels_x"   # Nhãn YOLOv8x

def run_master(from_minio=False):
    # 1. Khởi tạo
    if not os.path.exists(LABEL_DIR): os.makedirs(LABEL_DIR)
    print("⏳ Đang tải YOLOv8n...")
    model = YOLO(MODEL_PATH)

    if from_minio:
        # Lấy ảnh từ MinIO bucket processed
        from utils.database import MinIOClient
        minio = MinIOClient()
        img_names = minio.list_images(bucket="traffic-signs-processed")
        img_files = []
        for img_name in img_names:
            data = minio.download_image(img_name, bucket="traffic-signs-processed")
            if data:
                nparr = np.frombuffer(data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    img_files.append((img_name, img))
        print(f"🚀 BẮT ĐẦU XỬ LÝ {len(img_files)} ẢNH TỪ MINIO...")
    else:
        img_paths = glob.glob(os.path.join(IMG_DIR, "*.*"))
        img_files = []
        for img_path in img_paths:
            img = cv2.imread(img_path)
            if img is not None:
                img_files.append((os.path.basename(img_path), img))
        print(f"🚀 BẮT ĐẦU XỬ LÝ TOÀN BỘ {len(img_files)} ẢNH...")

    stats = {0:0, 1:0, 2:0, 3:0, 4:0}

    for img_name, img in tqdm(img_files):
        h_img, w_img = img.shape[:2]
        results = model(img, verbose=False, conf=CONF_THRESHOLD)
        candidates = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                crop = img[y1:y2, x1:x2]
                if crop.size == 0: continue
                cls_id = get_class_v2(crop)
                shape_name = get_shape_name(crop)
                area = (x2-x1)*(y2-y1)
                score = area * (0.1 if cls_id == 4 else 1.0)
                candidates.append({
                    'cls': cls_id,
                    'xyxy': [x1, y1, x2, y2],
                    'area': area,
                    'score': score,
                    'shape': shape_name
                })
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
        if len(final_boxes) > MAX_BOXES:
            final_boxes = final_boxes[:MAX_BOXES]
        if final_boxes:
            base_name = os.path.splitext(os.path.basename(img_name))[0]
            txt_path = os.path.join(LABEL_DIR, base_name + ".txt")
            with open(txt_path, "w") as f:
                # Ghi comment đầu file: # shape: shape1, shape2, ...
                shapes = [b['shape'] for b in final_boxes]
                f.write("# shapes: " + ", ".join(shapes) + "\n")
                for b in final_boxes:
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

    model_n = YOLO(MODEL_PATH)   # Sửa ở đây
    model_x = YOLO(MODEL_PATH_X)

    for img_path in tqdm(img_files):
        img = cv2.imread(img_path)
        if img is None: continue
        h_img, w_img = img.shape[:2]

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

        # Vẽ lên ảnh để so sánh
        img_compare = img.copy()
        img_compare = draw_boxes(img_compare, boxes_n, (0,255,0), "n:")
        img_compare = draw_boxes(img_compare, boxes_x, (0,0,255), "x:")

        # Lưu ảnh so sánh
        base_name = os.path.splitext(os.path.basename(img_path))[0]
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

        # Có thể thêm bước so sánh số lượng, vị trí, loại biển báo giữa 2 model
        # ... (tùy ý mở rộng)

    print(f"✅ Đã lưu ảnh so sánh tại: {COMPARE_DIR}/")
    print("Ảnh có khung xanh là YOLOv8n, khung đỏ là YOLOv8x.")

def run_dual_yolo(from_minio=False):
    # Khởi tạo
    for d in [LABEL_DIR_N, LABEL_DIR_X]:
        if not os.path.exists(d): os.makedirs(d)
    print("⏳ Đang tải YOLOv8n & YOLOv8x...")
    # DÙNG 2 MODEL GỐC, KHÔNG DÙNG best.pt
    model_n = YOLO(MODEL_PATH)
    model_x = YOLO(MODEL_PATH_X)

    # Lấy ảnh
    if from_minio:
        from utils.database import MinIOClient
        minio = MinIOClient()
        img_names = minio.list_images(bucket="traffic-signs-processed")
        img_files = []
        for img_name in img_names:
            data = minio.download_image(img_name, bucket="traffic-signs-processed")
            if data:
                nparr = np.frombuffer(data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    img_files.append((img_name, img))
        print(f"🚀 BẮT ĐẦU XỬ LÝ {len(img_files)} ẢNH TỪ MINIO...")
    else:
        img_paths = glob.glob(os.path.join(IMG_DIR, "*.*"))
        img_files = []
        for img_path in img_paths:
            img = cv2.imread(img_path)
            if img is not None:
                img_files.append((os.path.basename(img_path), img))
        print(f"🚀 BẮT ĐẦU XỬ LÝ TOÀN BỘ {len(img_files)} ẢNH...")

    stats_n = {0:0, 1:0, 2:0, 3:0, 4:0}
    stats_x = {0:0, 1:0, 2:0, 3:0, 4:0}

    for img_name, img in tqdm(img_files):
        h_img, w_img = img.shape[:2]
        # YOLOv8n
        results_n = model_n(img, verbose=False, conf=CONF_THRESHOLD)
        candidates_n = []
        for r in results_n:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                crop = img[y1:y2, x1:x2]
                if crop.size == 0: continue
                cls_id = get_class_v2(crop)
                area = (x2-x1)*(y2-y1)
                score = area * (0.1 if cls_id == 4 else 1.0)
                candidates_n.append({
                    'cls': cls_id,
                    'xyxy': [x1, y1, x2, y2],
                    'area': area,
                    'score': score
                })
        candidates_n.sort(key=lambda x: x['score'], reverse=True)
        final_boxes_n = []
        while candidates_n:
            curr = candidates_n.pop(0)
            is_dup = False
            for kept in final_boxes_n:
                if compute_iou(curr, kept) > IOU_THRESHOLD:
                    is_dup = True
                    break
            if not is_dup:
                final_boxes_n.append(curr)
        if len(final_boxes_n) > MAX_BOXES:
            final_boxes_n = final_boxes_n[:MAX_BOXES]
        if final_boxes_n:
            base_name = os.path.splitext(os.path.basename(img_name))[0]
            txt_path = os.path.join(LABEL_DIR_N, base_name + ".txt")
            with open(txt_path, "w") as f:
                for b in final_boxes_n:
                    x1, y1, x2, y2 = b['xyxy']
                    xc = ((x1+x2)/2) / w_img
                    yc = ((y1+y2)/2) / h_img
                    w = (x2-x1) / w_img
                    h = (y2-y1) / h_img
                    f.write(f"{b['cls']} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
                    stats_n[b['cls']] += 1

        # YOLOv8x
        results_x = model_x(img, verbose=False, conf=CONF_THRESHOLD)
        candidates_x = []
        for r in results_x:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                crop = img[y1:y2, x1:x2]
                if crop.size == 0: continue
                cls_id = get_class_v2(crop)
                area = (x2-x1)*(y2-y1)
                score = area * (0.1 if cls_id == 4 else 1.0)
                candidates_x.append({
                    'cls': cls_id,
                    'xyxy': [x1, y1, x2, y2],
                    'area': area,
                    'score': score
                })
        candidates_x.sort(key=lambda x: x['score'], reverse=True)
        final_boxes_x = []
        while candidates_x:
            curr = candidates_x.pop(0)
            is_dup = False
            for kept in final_boxes_x:
                if compute_iou(curr, kept) > IOU_THRESHOLD:
                    is_dup = True
                    break
            if not is_dup:
                final_boxes_x.append(curr)
        if len(final_boxes_x) > MAX_BOXES:
            final_boxes_x = final_boxes_x[:MAX_BOXES]
        if final_boxes_x:
            base_name = os.path.splitext(os.path.basename(img_name))[0]
            txt_path = os.path.join(LABEL_DIR_X, base_name + ".txt")
            with open(txt_path, "w") as f:
                for b in final_boxes_x:
                    x1, y1, x2, y2 = b['xyxy']
                    xc = ((x1+x2)/2) / w_img
                    yc = ((y1+y2)/2) / h_img
                    w = (x2-x1) / w_img
                    h = (y2-y1) / h_img
                    f.write(f"{b['cls']} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
                    stats_x[b['cls']] += 1

    print("\n" + "="*50)
    print("✅ HOÀN THÀNH DUAL YOLO!")
    print("📊 Thống kê YOLOv8n:")
    print(f"   0 - Cấm:       {stats_n[0]}")
    print(f"   1 - Nguy hiểm: {stats_n[1]}")
    print(f"   2 - Hiệu lệnh: {stats_n[2]}")
    print(f"   3 - Chỉ dẫn:   {stats_n[3]}")
    print(f"   4 - Khác:      {stats_n[4]}")
    print(f"👉 Tổng số vật thể YOLOv8n: {sum(stats_n.values())}")
    print("-"*30)
    print("📊 Thống kê YOLOv8x:")
    print(f"   0 - Cấm:       {stats_x[0]}")
    print(f"   1 - Nguy hiểm: {stats_x[1]}")
    print(f"   2 - Hiệu lệnh: {stats_x[2]}")
    print(f"   3 - Chỉ dẫn:   {stats_x[3]}")
    print(f"   4 - Khác:      {stats_x[4]}")
    print(f"👉 Tổng số vật thể YOLOv8x: {sum(stats_x.values())}")
    print("="*50)

if __name__ == "__main__":
    # Thêm lựa chọn chạy so sánh
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--compare", action="store_true", help="So sánh YOLOv8n vs YOLOv8x")
    parser.add_argument("--from-minio", action="store_true", help="Lấy ảnh trực tiếp từ MinIO bucket processed")
    parser.add_argument("--dual-yolo", action="store_true", help="Nhận diện song song bằng cả YOLOv8n & YOLOv8x")
    args = parser.parse_args()
    if args.compare:
        run_compare_yolo()
    elif args.dual_yolo:
        run_dual_yolo(from_minio=args.from_minio)
    else:
        run_master(from_minio=args.from_minio)