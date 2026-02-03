import os
import cv2
import glob
import numpy as np
from tqdm import tqdm

# --- CẤU HÌNH QUAN TRỌNG ---
IMG_DIR = "datasets/images"
LABEL_DIR = "datasets/labels"
IOU_THRESHOLD = 0.75   # Ngưỡng lọc trùng mạnh tay (chồng 75% là xóa)
MAX_BOXES_PER_IMG = 5  # Giới hạn tối đa 5 biển/ảnh

# --- DẢI MÀU HSV (V2) ---
LOWER_RED1 = np.array([0, 50, 50])
UPPER_RED1 = np.array([15, 255, 255])
LOWER_RED2 = np.array([160, 50, 50])
UPPER_RED2 = np.array([180, 255, 255])

LOWER_BLUE = np.array([90, 50, 50])
UPPER_BLUE = np.array([150, 255, 255])

LOWER_YELLOW = np.array([15, 50, 50])
UPPER_YELLOW = np.array([35, 255, 255])

def get_sign_class_fast_v2(img_crop):
    """Phân loại màu sắc + Logic hình học V2"""
    h_img, w_img = img_crop.shape[:2]
    area_total = h_img * w_img
    if area_total == 0: return 4

    hsv = cv2.cvtColor(img_crop, cv2.COLOR_BGR2HSV)

    mask_red = cv2.inRange(hsv, LOWER_RED1, UPPER_RED1) + cv2.inRange(hsv, LOWER_RED2, UPPER_RED2)
    mask_blue = cv2.inRange(hsv, LOWER_BLUE, UPPER_BLUE)
    mask_yellow = cv2.inRange(hsv, LOWER_YELLOW, UPPER_YELLOW)

    r_count = cv2.countNonZero(mask_red)
    b_count = cv2.countNonZero(mask_blue)
    y_count = cv2.countNonZero(mask_yellow)
    threshold = area_total * 0.05

    # 1. Nguy hiểm (Vàng)
    if y_count > threshold and y_count > b_count: return 1
    # 2. Đỏ (Cấm/Nguy hiểm)
    if r_count > threshold and r_count > b_count:
        return 1 if (r_count / area_total) < 0.35 else 0
    # 3. Xanh (Chỉ dẫn/Hiệu lệnh)
    elif b_count > threshold:
        return 3 if (b_count / area_total) > 0.80 else 2
    
    return 4

def compute_iou(box1, box2):
    """Tính độ chồng lấn (IoU)"""
    # box format: [xc, yc, w, h]
    b1_x1, b1_y1 = box1[0] - box1[2]/2, box1[1] - box1[3]/2
    b1_x2, b1_y2 = box1[0] + box1[2]/2, box1[1] + box1[3]/2
    b2_x1, b2_y1 = box2[0] - box2[2]/2, box2[1] - box2[3]/2
    b2_x2, b2_y2 = box2[0] + box2[2]/2, box2[1] + box2[3]/2

    xi1, yi1 = max(b1_x1, b2_x1), max(b1_y1, b2_y1)
    xi2, yi2 = min(b1_x2, b2_x2), min(b1_y2, b2_y2)
    
    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    b1_area = (b1_x2 - b1_x1) * (b1_y2 - b1_y1)
    b2_area = (b2_x2 - b2_x1) * (b2_y2 - b2_y1)
    union_area = b1_area + b2_area - inter_area
    
    return inter_area / union_area if union_area > 0 else 0

def run_pipeline_aggressive():
    txt_files = glob.glob(os.path.join(LABEL_DIR, "*.txt"))
    if not txt_files: return print("❌ Không tìm thấy file nhãn!")

    print(f"🔥 BẮT ĐẦU: PHÂN LOẠI + LỌC TRÙNG MẠNH TAY...")
    print(f"   - IoU Threshold: {IOU_THRESHOLD}")
    print(f"   - Max Boxes/Image: {MAX_BOXES_PER_IMG}")
    
    stats = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    total_removed = 0
    
    for txt_path in tqdm(txt_files):
        # 1. Load ảnh
        base = os.path.splitext(os.path.basename(txt_path))[0]
        img_p = os.path.join(IMG_DIR, base + ".jpg")
        if not os.path.exists(img_p): img_p = img_p.replace(".jpg", ".png")
        if not os.path.exists(img_p): continue

        img = cv2.imread(img_p)
        if img is None: continue
        h_img, w_img = img.shape[:2]

        with open(txt_path, "r") as f:
            lines = f.readlines()
        
        # 2. Xử lý tất cả các box (Phân loại ngay lập tức)
        processed_boxes = []
        for line in lines:
            parts = line.split()
            if len(parts) < 5: continue
            bbox = list(map(float, parts[1:5])) # xc, yc, w, h
            xc, yc, w, h = bbox
            
            # Crop
            x1 = int((xc - w/2) * w_img); y1 = int((yc - h/2) * h_img)
            x2 = int((xc + w/2) * w_img); y2 = int((yc + h/2) * h_img)
            x1=max(0,x1); y1=max(0,y1); x2=min(w_img,x2); y2=min(h_img,y2)
            
            if x2 <= x1 or y2 <= y1: continue
            
            crop = img[y1:y2, x1:x2]
            
            # Phân loại V2
            cls_id = get_sign_class_fast_v2(crop)
            
            # Tính "Điểm ưu tiên" (Priority Score)
            # Box to thì tốt, nhưng Box Class Xịn (0,1,2,3) ưu tiên hơn Box Rác (4)
            area = w * h
            priority_score = area * 100 if cls_id != 4 else area
            
            processed_boxes.append({
                'cls': cls_id,
                'bbox': bbox,
                'score': priority_score
            })

        # 3. Thuật toán Lọc trùng (NMS)
        # Sắp xếp theo điểm ưu tiên giảm dần (Box xịn + to nằm trên)
        processed_boxes.sort(key=lambda x: x['score'], reverse=True)
        
        keep_boxes = []
        while processed_boxes:
            current = processed_boxes.pop(0)
            is_duplicate = False
            
            for kept in keep_boxes:
                # Nếu chồng lấn quá ngưỡng IoU -> Xóa
                if compute_iou(current['bbox'], kept['bbox']) > IOU_THRESHOLD:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                keep_boxes.append(current)

        # 4. Giới hạn số lượng (Chỉ giữ 5 cái tốt nhất)
        original_count = len(lines)
        if len(keep_boxes) > MAX_BOXES_PER_IMG:
            keep_boxes = keep_boxes[:MAX_BOXES_PER_IMG]
        
        total_removed += (original_count - len(keep_boxes))

        # 5. Ghi đè file
        final_lines = []
        for box in keep_boxes:
            c = box['cls']
            b = box['bbox']
            stats[c] += 1
            final_lines.append(f"{c} {b[0]} {b[1]} {b[2]} {b[3]}\n")

        with open(txt_path, "w") as f:
            f.writelines(final_lines)

    print("\n" + "="*50)
    print(f"✅ HOÀN TẤT QUY TRÌNH!")
    print(f"✂️ Đã cắt bỏ: {total_removed} box trùng/rác.")
    print("-" * 30)
    print("📊 THỐNG KÊ CUỐI CÙNG (Mong đợi khoảng 3000-5000):")
    print(f"   0 - Cấm:       {stats[0]}")
    print(f"   1 - Nguy hiểm: {stats[1]}")
    print(f"   2 - Hiệu lệnh: {stats[2]}")
    print(f"   3 - Chỉ dẫn:   {stats[3]}")
    print(f"   4 - Khác:      {stats[4]}")
    print("="*50)
    print(f"👉 Tổng cộng: {sum(stats.values())} vật thể / {len(txt_files)} ảnh")

if __name__ == "__main__":
    run_pipeline_aggressive()