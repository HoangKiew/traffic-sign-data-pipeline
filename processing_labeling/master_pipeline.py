import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import cv2
import numpy as np
from tqdm import tqdm

# --- CONFIG ---
LABEL_DIR = "datasets/labels"
LABEL_DIR_N = "datasets/labels_n"
LABEL_DIR_X = "datasets/labels_x"
COMPARE_DIR = "compare_results"

def get_class_v2(img_crop):
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

def get_minio_images():
    from utils.database import MinIOClient
    minio = MinIOClient()
    img_names = minio.list_images(bucket="traffic-signs-crop-n")
    img_files = []
    for img_name in img_names:
        data = minio.download_image(img_name, bucket="traffic-signs-crop-n")
        if data:
            nparr = np.frombuffer(data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                img_files.append((img_name, img))
    return img_files

def run_single_yolo():
    os.makedirs(LABEL_DIR, exist_ok=True)
    img_files = get_minio_images()
    print(f"🚀 PHÂN LOẠI {len(img_files)} ẢNH CROP TỪ MINIO (KHÔNG DETECT LẠI)...")
    stats = {0:0, 1:0, 2:0, 3:0, 4:0}
    for img_name, img in tqdm(img_files):
        h_img, w_img = img.shape[:2]
        cls_id = get_class_v2(img)
        base_name = os.path.splitext(os.path.basename(img_name))[0]
        txt_path = os.path.join(LABEL_DIR, base_name + ".txt")
        # Gán nhãn: 1 box toàn ảnh crop, class theo màu
        with open(txt_path, "w") as f:
            xc, yc, w, h = 0.5, 0.5, 1.0, 1.0
            f.write(f"{cls_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
            stats[cls_id] += 1
    print("\n" + "="*50)
    print("✅ HOÀN THÀNH PHÂN LOẠI CROP!")
    print("📊 Thống kê cuối cùng:")
    print(f"   0 - Cấm:       {stats[0]}")
    print(f"   1 - Nguy hiểm: {stats[1]}")
    print(f"   2 - Hiệu lệnh: {stats[2]}")
    print(f"   3 - Chỉ dẫn:   {stats[3]}")
    print(f"   4 - Khác:      {stats[4]}")
    print(f"👉 Tổng số vật thể: {sum(stats.values())}")
    print("="*50)

def run_dual_yolo():
    os.makedirs(LABEL_DIR_N, exist_ok=True)
    os.makedirs(LABEL_DIR_X, exist_ok=True)
    img_files = get_minio_images()
    print(f"🚀 PHÂN LOẠI {len(img_files)} ẢNH CROP TỪ MINIO (DUAL YOLO GIẢ LẬP)...")
    stats_n = {0:0, 1:0, 2:0, 3:0, 4:0}
    stats_x = {0:0, 1:0, 2:0, 3:0, 4:0}
    for img_name, img in tqdm(img_files):
        h_img, w_img = img.shape[:2]
        # Giả lập: dùng cùng 1 hàm phân loại màu cho cả 2 model (thực tế sẽ detect bằng 2 model khác nhau)
        cls_id_n = get_class_v2(img)  # YOLOv8n
        cls_id_x = get_class_v2(img)  # YOLOv8x (ở đây chỉ demo, thực tế phải detect riêng)
        base_name = os.path.splitext(os.path.basename(img_name))[0]
        txt_path_n = os.path.join(LABEL_DIR_N, base_name + ".txt")
        txt_path_x = os.path.join(LABEL_DIR_X, base_name + ".txt")
        with open(txt_path_n, "w") as f_n, open(txt_path_x, "w") as f_x:
            xc, yc, w, h = 0.5, 0.5, 1.0, 1.0
            f_n.write(f"{cls_id_n} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
            f_x.write(f"{cls_id_x} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
            stats_n[cls_id_n] += 1
            stats_x[cls_id_x] += 1
    print("\n" + "="*50)
    print("✅ HOÀN THÀNH PHÂN LOẠI CROP (DUAL YOLO)!")
    print("📊 Thống kê YOLOv8n:")
    print(f"   0 - Cấm:       {stats_n[0]}")
    print(f"   1 - Nguy hiểm: {stats_n[1]}")
    print(f"   2 - Hiệu lệnh: {stats_n[2]}")
    print(f"   3 - Chỉ dẫn:   {stats_n[3]}")
    print(f"   4 - Khác:      {stats_n[4]}")
    print(f"👉 Tổng số vật thể: {sum(stats_n.values())}")
    print("-"*50)
    print("📊 Thống kê YOLOv8x:")
    print(f"   0 - Cấm:       {stats_x[0]}")
    print(f"   1 - Nguy hiểm: {stats_x[1]}")
    print(f"   2 - Hiệu lệnh: {stats_x[2]}")
    print(f"   3 - Chỉ dẫn:   {stats_x[3]}")
    print(f"   4 - Khác:      {stats_x[4]}")
    print(f"👉 Tổng số vật thể: {sum(stats_x.values())}")
    print("="*50)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dual-yolo", action="store_true", help="Chạy song song YOLOv8n và YOLOv8x (dual YOLO)")
    parser.add_argument("--single-yolo", action="store_true", help="Chỉ chạy YOLOv8n (single YOLO)")
    args = parser.parse_args()
    if args.dual_yolo:
        run_dual_yolo()
    else:
        run_single_yolo()