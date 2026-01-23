import os
import sys
import hashlib
import cv2
import numpy as np
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# Import MinIO
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.database import MinIOClient
from config.config import MINIO_BUCKET_RAW

# --- CẤU HÌNH BỘ LỌC ---
MIN_FILE_SIZE_KB = 10      # Dưới 10KB -> Xóa
MIN_RESOLUTION = (100, 100) # Nhỏ hơn 100x100px -> Xóa
ASPECT_RATIO_RANGE = (0.5, 2.5) # Chỉ giữ lại ảnh có tỷ lệ từ 1:2 đến 2.5:1

class FastFilter:
    def __init__(self):
        self.minio = MinIOClient()
        self.deleted_count = 0
        self.hashes = set()
        self.duplicate_count = 0

    def calculate_hash(self, image_bytes):
        """Tính mã hash MD5 để tìm ảnh trùng"""
        return hashlib.md5(image_bytes).hexdigest()

    def process_single_image(self, img_name):
        """Xử lý 1 ảnh: Kiểm tra Size -> Hash -> Resolution -> Ratio"""
        try:
            # 1. Tải ảnh (Blob)
            data = self.minio.download_image(img_name)
            if not data: return "error"

            # --- CHECK 1: KÍCH THƯỚC FILE (Siêu nhanh) ---
            size_kb = len(data) / 1024
            if size_kb < MIN_FILE_SIZE_KB:
                self.minio.client.remove_object(MINIO_BUCKET_RAW, img_name)
                return "deleted_small"

            # --- CHECK 2: TRÙNG LẶP (Deduplication) ---
            img_hash = self.calculate_hash(data)
            if img_hash in self.hashes:
                self.minio.client.remove_object(MINIO_BUCKET_RAW, img_name)
                return "deleted_duplicate"
            self.hashes.add(img_hash) # Thêm vào bộ nhớ đệm

            # --- CHECK 3: NỘI DUNG ẢNH (Resolution & Ratio) ---
            # Chỉ decode ảnh nếu qua được 2 bước trên (tiết kiệm CPU)
            nparr = np.frombuffer(data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                self.minio.client.remove_object(MINIO_BUCKET_RAW, img_name)
                return "deleted_error"

            h, w, _ = img.shape
            
            # Check độ phân giải
            if w < MIN_RESOLUTION[0] or h < MIN_RESOLUTION[1]:
                self.minio.client.remove_object(MINIO_BUCKET_RAW, img_name)
                return "deleted_low_res"

            # Check tỷ lệ khung hình
            ratio = w / h
            if ratio < ASPECT_RATIO_RANGE[0] or ratio > ASPECT_RATIO_RANGE[1]:
                self.minio.client.remove_object(MINIO_BUCKET_RAW, img_name)
                return "deleted_bad_ratio"

            return "kept"

        except Exception as e:
            return "error"

    def run(self):
        print(f"🚀 BẮT ĐẦU LỌC NHANH (FAST FILTER)")
        print(f"   • Min Size: {MIN_FILE_SIZE_KB} KB")
        print(f"   • Min Res:  {MIN_RESOLUTION}")
        print(f"   • Ratio:    {ASPECT_RATIO_RANGE}")
        print("-" * 50)

        all_images = self.minio.list_images()
        print(f"📦 Tìm thấy {len(all_images)} ảnh trong kho.")

        stats = {
            "kept": 0,
            "deleted_small": 0,
            "deleted_duplicate": 0,
            "deleted_low_res": 0,
            "deleted_bad_ratio": 0,
            "deleted_error": 0,
            "error": 0
        }

        # Chạy đa luồng (Multi-threading) để tăng tốc độ I/O
        # MinIO xử lý I/O rất tốt nên ta có thể chạy 8-16 luồng
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(tqdm(executor.map(self.process_single_image, all_images), total=len(all_images), unit="img"))

        # Tổng hợp kết quả
        for res in results:
            if res in stats:
                stats[res] += 1

        print("\n" + "="*50)
        print("📊 KẾT QUẢ SAU KHI LỌC NHANH:")
        print(f"   ✅ Giữ lại:        {stats['kept']} ảnh")
        print(f"   🗑️ Xóa (Quá nhỏ):   {stats['deleted_small']}")
        print(f"   🗑️ Xóa (Trùng lặp): {stats['deleted_duplicate']}")
        print(f"   🗑️ Xóa (Độ phân giải thấp): {stats['deleted_low_res']}")
        print(f"   🗑️ Xóa (Tỷ lệ dị dạng):     {stats['deleted_bad_ratio']}")
        print(f"   ⚠️ Lỗi file:        {stats['deleted_error']}")
        print("="*50)

if __name__ == "__main__":
    filter_tool = FastFilter()
    filter_tool.run()