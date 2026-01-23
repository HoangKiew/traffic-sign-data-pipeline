import os
import cv2
import glob
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO

# --- CẤU HÌNH ---
IMG_DIR = "datasets/images"       # Thư mục ảnh sạch
LABEL_DIR = "datasets/labels"     # Thư mục nhãn (Hãy đảm bảo nó TRỐNG)
MODEL_PATH = "yolov8n.pt"         # Model YOLO gốc
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
    
    img_files = glob.glob(os.path.join(IMG_DIR, "*.*"))
    print(f"🚀 BẮT ĐẦU XỬ LÝ TOÀN BỘ {len(img_files)} ẢNH...")

    stats = {0:0, 1:0, 2:0, 3:0, 4:0}
    
    for img_path in tqdm(img_files):
        # Đọc ảnh
        img = cv2.imread(img_path)
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
            base_name = os.path.splitext(os.path.basename(img_path))[0]
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

if __name__ == "__main__":
    run_master()