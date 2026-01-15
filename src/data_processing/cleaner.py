import pandas as pd
import numpy as np
from pathlib import Path
from PIL import Image
import os
import hashlib
from sklearn.model_selection import train_test_split
from tqdm import tqdm

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("opencv-python chưa cài đặt. Chạy: pip install opencv-python để detect ảnh mờ.")

try:
    from pymongo import MongoClient
    from bson import Binary
    HAS_MONGO = True
except ImportError:
    HAS_MONGO = False
    print("pymongo chưa cài đặt. Chạy: pip install pymongo")

# Luon dung config, khong fallback hard-code URI
from config import CONNECTION_STRING, DATABASE_NAME, COLLECTION_NAME

try:
    import imagehash
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False
    print("imagehash chưa cài đặt. Chạy: pip install imagehash")


class TrafficSignProcessor:
    """Xử lý toàn bộ: clean + split + resize ảnh biển báo giao thông"""
    
    def __init__(self, raw_dir='data/raw', metadata_path='data/metadata.csv'):
        self.raw_dir = Path(raw_dir)
        self.metadata_path = Path(metadata_path)
        self.df = None
        self.train_df = None
        self.val_df = None
        self.test_df = None
    
    def create_metadata(self):
        """Tạo metadata từ thư mục ảnh thô"""
        print("Đang tạo metadata từ raw images...")
        
        data = []
        categories = ['prohibitory', 'warning', 'mandatory', 'informative']
        
        for category in categories:
            category_path = self.raw_dir / category
            if not category_path.exists():
                continue
            
            for img_file in category_path.glob('*.*'):
                if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    try:
                        with Image.open(img_file) as img:
                            data.append({
                                'image_path': str(img_file),
                                'filename': img_file.name,
                                'category': category,
                                'width': img.width,
                                'height': img.height,
                                'format': img.format,
                                'mode': img.mode,
                                'size_kb': img_file.stat().st_size / 1024
                            })
                    except Exception as e:
                        print(f"Lỗi đọc {img_file.name}: {e}")
        
        self.df = pd.DataFrame(data)
        print(f"Đã tạo metadata cho {len(self.df)} images")
        return self.df
    
    def add_md5_hash(self):
        """Thêm MD5 hash để phát hiện trùng lặp hoàn toàn"""
        print("\nĐang tính MD5 hash...")
        
        def get_md5(img_path):
            try:
                with open(img_path, 'rb') as f:
                    return hashlib.md5(f.read()).hexdigest()
            except:
                return None
        
        self.df['md5_hash'] = self.df['image_path'].apply(get_md5)
        print(f"Đã tính MD5 hash cho {len(self.df)} images")
    
    def add_perceptual_hash(self):
        """Thêm perceptual hash để phát hiện ảnh tương tự"""
        if not HAS_IMAGEHASH:
            print("Bỏ qua perceptual hash (chưa cài imagehash)")
            return
        
        print("\nĐang tính perceptual hash...")
        
        def get_phash(img_path):
            try:
                img = Image.open(img_path)
                return str(imagehash.average_hash(img))
            except:
                return None
        
        self.df['phash'] = self.df['image_path'].apply(get_phash)
        print(f"Đã tính perceptual hash cho {len(self.df)} images")
    
    def find_exact_duplicates(self):
        """Tìm và báo cáo ảnh trùng lặp hoàn toàn"""
        if 'md5_hash' not in self.df.columns:
            print("Chưa có MD5 hash. Gọi add_md5_hash() trước.")
            return
        
        print("\nTìm exact duplicates (MD5)...")
        duplicates = self.df[self.df.duplicated(subset=['md5_hash'], keep=False)]
        
        if len(duplicates) == 0:
            print("Không có ảnh trùng lặp")
        else:
            print(f"Tìm thấy {len(duplicates)} ảnh trùng lặp:")
            for hash_val, group in duplicates.groupby('md5_hash'):
                print(f"  Hash {hash_val[:8]}...:")
                for _, row in group.iterrows():
                    print(f"    - {row['filename']}")
    
    def find_similar_images(self, threshold=5):
        """Tìm và báo cáo ảnh tương tự (perceptual hash)"""
        if not HAS_IMAGEHASH or 'phash' not in self.df.columns:
            print("Không thể tìm similar images (chưa có phash)")
            return
        
        print(f"\nTìm similar images (threshold={threshold})...")
        
        similar_groups = []
        processed = set()
        
        for i, row1 in self.df.iterrows():
            if i in processed or pd.isna(row1['phash']):
                continue
            
            group = [i]
            hash1 = imagehash.hex_to_hash(row1['phash'])
            
            for j, row2 in self.df.iterrows():
                if i >= j or j in processed or pd.isna(row2['phash']):
                    continue
                
                hash2 = imagehash.hex_to_hash(row2['phash'])
                distance = hash1 - hash2
                
                if distance <= threshold:
                    group.append(j)
                    processed.add(j)
            
            if len(group) > 1:
                similar_groups.append(group)
        
        if len(similar_groups) == 0:
            print("Không có ảnh tương tự")
        else:
            print(f"Tìm thấy {len(similar_groups)} nhóm ảnh tương tự:")
            for i, group in enumerate(similar_groups, 1):
                print(f"  Nhóm {i}:")
                for idx in group:
                    row = self.df.iloc[idx]
                    print(f"    - {row['filename']} ({row['width']}x{row['height']})")
    
    # ───────────────────────────
    # EDA / CHECKING (theo slide)
    # ───────────────────────────
    def analyze_data(self):
        """Thống kê tổng quan metadata (EDA cơ bản)."""
        print("\nPHÂN TÍCH TỔNG QUAN (EDA)")
        print("-" * 60)
        if self.df is None or self.df.empty:
            print("Metadata trống. Gọi create_metadata() trước.")
            return
        print("Số ảnh theo category:")
        print(self.df['category'].value_counts())
        print("\nThống kê width / height / size_kb:")
        print(self.df[['width', 'height', 'size_kb']].describe().round(2))

    def check_missing_values(self):
        """Kiểm tra giá trị thiếu trong metadata."""
        print("\nKIỂM TRA GIÁ TRỊ THIẾU")
        print("-" * 60)
        if self.df is None:
            print("Metadata trống. Gọi create_metadata() trước.")
            return
        missing = self.df.isnull().sum()
        if missing.sum() == 0:
            print("Không có giá trị thiếu.")
        else:
            print(missing[missing > 0])

    def detect_outliers(self):
        """Phát hiện outlier bằng IQR (không xóa, chỉ báo cáo)."""
        print("\nPHÁT HIỆN OUTLIER (IQR)")
        print("-" * 60)
        if self.df is None:
            print("Metadata trống. Gọi create_metadata() trước.")
            return
        for col in ['width', 'height', 'size_kb']:
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            outliers = self.df[(self.df[col] < lower) | (self.df[col] > upper)]
            print(f"{col}: {len(outliers)} outliers")

    def detect_and_remove_blurry(self, threshold: float = 100.0):
        """
        Phát hiện và loại bỏ ảnh mờ dựa trên Laplacian variance.
        threshold càng cao → lọc gắt hơn.
        """
        if not HAS_CV2:
            print("\nBỏ qua detect ảnh mờ (opencv-python chưa cài).")
            return
        if self.df is None or self.df.empty:
            print("\nMetadata trống. Gọi create_metadata() trước.")
            return

        print("\nPHÁT HIỆN ẢNH MỜ (Laplacian variance)")
        print("-" * 60)

        def lap_var(path: str):
            try:
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    return np.nan
                return float(cv2.Laplacian(img, cv2.CV_64F).var())
            except Exception:
                return np.nan

        self.df['laplacian_var'] = self.df['image_path'].apply(lap_var)
        blurry_mask = self.df['laplacian_var'] < threshold
        n_blurry = blurry_mask.sum()
        print(f"Tổng ảnh mờ (var < {threshold:.1f}): {n_blurry}")

        if n_blurry > 0:
            before = len(self.df)
            self.df = self.df[~blurry_mask].reset_index(drop=True)
            print(f"Đã loại bỏ {before - len(self.df)} ảnh mờ. Còn lại: {len(self.df)} ảnh.")
        else:
            print("Không phát hiện ảnh mờ nào cần loại bỏ.")

    # ───────────────────────────
    # CLEANING
    # ───────────────────────────
    def clean_data(self, remove_outliers=False, min_size=32):
        """Làm sạch dữ liệu: xóa trùng, ảnh nhỏ, outliers (nếu chọn)"""
        print("\n" + "="*60)
        print("CLEANING DATA")
        print("="*60)
        
        original_size = len(self.df)
        
        # Xóa trùng theo tên file
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=['filename'])
        print(f"Đã loại bỏ {before - len(self.df)} duplicates (by filename)")
        
        # Xóa trùng exact bằng MD5
        if 'md5_hash' in self.df.columns:
            before = len(self.df)
            self.df = self.df.drop_duplicates(subset=['md5_hash'], keep='first')
            removed = before - len(self.df)
            if removed > 0:
                print(f"Đã loại bỏ {removed} exact duplicates (by MD5)")
        
        # Xóa ảnh quá nhỏ
        before = len(self.df)
        self.df = self.df[(self.df['width'] >= min_size) & (self.df['height'] >= min_size)]
        print(f"Đã loại bỏ {before - len(self.df)} ảnh quá nhỏ")
        
        # Xóa outliers nếu chọn
        if remove_outliers:
            Q1_w = self.df['width'].quantile(0.25)
            Q3_w = self.df['width'].quantile(0.75)
            IQR_w = Q3_w - Q1_w
            outliers_w = self.df[(self.df['width'] < Q1_w - 1.5*IQR_w) | (self.df['width'] > Q3_w + 1.5*IQR_w)]
            
            Q1_h = self.df['height'].quantile(0.25)
            Q3_h = self.df['height'].quantile(0.75)
            IQR_h = Q3_h - Q1_h
            outliers_h = self.df[(self.df['height'] < Q1_h - 1.5*IQR_h) | (self.df['height'] > Q3_h + 1.5*IQR_h)]
            
            outlier_indices = pd.concat([outliers_w, outliers_h]).index.unique()
            before = len(self.df)
            self.df = self.df.drop(outlier_indices, errors='ignore')
            print(f"Đã loại bỏ {before - len(self.df)} outliers")
        
        print(f"\nKết quả: {original_size} → {len(self.df)} images")
    
    # ───────────────────────────
    # DATA INTEGRATION → MongoDB
    # ───────────────────────────
    def upload_to_mongodb(self, drop_existing: bool = False, include_image: bool = True):
        """
        Đẩy metadata (và tùy chọn nội dung ảnh) lên MongoDB.
        - drop_existing: True → xóa dữ liệu cũ trong collection trước khi insert.
        - include_image: True → lưu cả bytes ảnh (Binary); False → chỉ lưu metadata.
        """
        if not HAS_MONGO:
            print("Bỏ qua upload MongoDB (pymongo chưa cài).")
            return
        if self.df is None or self.df.empty:
            print("Không có metadata để upload. Gọi create_metadata()/clean_data() trước.")
            return

        print("\n" + "=" * 60)
        print("UPLOAD DỮ LIỆU LÊN MONGODB (Data Integration)")
        print("=" * 60)

        client = MongoClient(CONNECTION_STRING)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        if drop_existing:
            collection.delete_many({})
            print("Đã xóa toàn bộ document cũ trong collection.")

        docs = []
        for _, row in self.df.iterrows():
            doc = {
                'filename': row['filename'],
                'category': row['category'],
                'width': int(row['width']),
                'height': int(row['height']),
                'format': row.get('format'),
                'mode': row.get('mode'),
                'size_kb': float(row['size_kb']),
                'image_path': row['image_path'],
            }
            if 'md5_hash' in self.df.columns:
                doc['md5_hash'] = row['md5_hash']
            if include_image:
                try:
                    with open(row['image_path'], 'rb') as f:
                        doc['image'] = Binary(f.read())
                except Exception as e:
                    print(f"Lỗi đọc file {row['image_path']}: {e}")
            docs.append(doc)

        if docs:
            collection.insert_many(docs)
            print(f"Đã upload {len(docs)} documents vào MongoDB "
                  f"({DATABASE_NAME}.{COLLECTION_NAME}).")
        else:
            print("Không có document nào để upload.")

        client.close()
    
    def split_dataset(self, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        """Chia dataset thành train/val/test theo category"""
        print("\n" + "="*60)
        print("CHIA DATASET")
        print("="*60)
        
        train_data, val_data, test_data = [], [], []
        
        for category in self.df['category'].unique():
            cat_df = self.df[self.df['category'] == category]
            n = len(cat_df)
            
            if n < 6:
                print(f"  {category}: {n} ảnh → Tất cả vào train")
                train_data.append(cat_df)
                continue
            
            if n < 15:
                print(f"  {category}: {n} ảnh → Train/Test (80/20)")
                train, test = train_test_split(cat_df, test_size=0.2, random_state=42)
                train_data.append(train)
                test_data.append(test)
                continue
            
            print(f"  {category}: {n} ảnh → Train/Val/Test (70/15/15)")
            train, temp = train_test_split(cat_df, test_size=val_ratio+test_ratio, random_state=42)
            val, test = train_test_split(temp, test_size=test_ratio/(val_ratio+test_ratio), random_state=42)
            train_data.append(train)
            val_data.append(val)
            test_data.append(test)
        
        self.train_df = pd.concat(train_data, ignore_index=True)
        self.val_df = pd.concat(val_data, ignore_index=True)
        self.test_df = pd.concat(test_data, ignore_index=True)
        
        print(f"Train: {len(self.train_df)} ({train_ratio*100:.0f}%)")
        print(f"Val:   {len(self.val_df)} ({val_ratio*100:.0f}%)")
        print(f"Test:  {len(self.test_df)} ({test_ratio*100:.0f}%)")
    
    def resize_and_save(self, target_size=(64, 64), output_dir='data/processed'):
        """Resize và lưu ảnh vào thư mục processed"""
        print("\n" + "="*60)
        print("RESIZE VÀ LƯU ẢNH")
        print("="*60)
        
        out_path = Path(output_dir)
        for split in ['train', 'val', 'test']:
            for cat in self.df['category'].unique():
                (out_path / split / cat).mkdir(parents=True, exist_ok=True)
        
        for split_name, split_df in [('train', self.train_df), ('val', self.val_df), ('test', self.test_df)]:
            print(f"\nĐang xử lý {split_name} set...")
            count = 0
            
            for _, row in tqdm(split_df.iterrows(), total=len(split_df), desc=split_name):
                try:
                    img = Image.open(row['image_path'])
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img_resized = img.resize(target_size, Image.Resampling.LANCZOS)
                    
                    save_path = out_path / split_name / row['category'] / f"{Path(row['filename']).stem}.png"
                    img_resized.save(save_path, 'PNG')
                    count += 1
                except Exception as e:
                    print(f"Lỗi xử lý {row['filename']}: {e}")
            
            print(f"Đã xử lý {count}/{len(split_df)} ảnh")
        
        print(f"\nĐã lưu tất cả ảnh vào: {out_path}")


class DataCleaner(TrafficSignProcessor):
    """Giữ tên class cũ để main.py sử dụng cho bước Preprocessing."""
    pass


def main():
    print("Pipeline Tổng hợp: Cleaning + Preprocessing")
    print("="*70)
    
    processor = TrafficSignProcessor()
    
    # 1. Cleaning
    processor.create_metadata()
    processor.add_md5_hash()
    processor.add_perceptual_hash()
    processor.find_exact_duplicates()
    processor.find_similar_images(threshold=5)
    processor.analyze_data()
    processor.check_missing_values()
    processor.detect_outliers()
    processor.clean_data(remove_outliers=False)
    processor.upload_to_mongodb(drop_existing=True, include_image=True)
    
    # 2. Split & Preprocess
    processor.split_dataset()
    processor.resize_and_save(target_size=(64, 64))
    
    print("\n" + "="*70)
    print("HOÀN TẤT!")
    print("="*70)
    print(f"Tổng ảnh sau clean: {len(processor.df)}")
    print(f"Train/Val/Test: {len(processor.train_df)} / {len(processor.val_df)} / {len(processor.test_df)}")
    print("Metadata nằm trong MongoDB (traffic_signs_db.images)")
    print("Ảnh đã xử lý: data/processed/")


if __name__ == '__main__':
    main()