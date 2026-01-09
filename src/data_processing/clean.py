"""
Data Cleaning Module
Xử lý và làm sạch dữ liệu theo workflow trong slide
Bổ sung: MD5 Hash và Perceptual Hash để phát hiện duplicates & similar images
"""

import pandas as pd
import numpy as np
from pathlib import Path
from PIL import Image
import os
import hashlib

try:
    import imagehash
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False
    print(" imagehash chưa cài đặt. Chạy: pip install imagehash")


class DataCleaner:
    """Clean và validate traffic sign dataset"""
    
    def __init__(self, data_dir='data/raw'):
        self.data_dir = Path(data_dir)
        self.df = None
    
    def create_metadata(self):
        """
        Tạo metadata DataFrame từ raw images
        Scan tất cả images và thu thập thông tin
        """
        print(" Đang tạo metadata từ raw images...")
        
        data = []
        categories = ['prohibitory', 'warning', 'mandatory', 'informative']
        
        for category in categories:
            category_path = self.data_dir / category
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
                        print(f"⚠️  Lỗi đọc {img_file.name}: {e}")
        
        self.df = pd.DataFrame(data)
        print(f"✓ Đã tạo metadata cho {len(self.df)} images")
        return self.df
    
    def add_md5_hash(self):
        """
        Thêm MD5 hash để phát hiện exact duplicates
        """
        print("\n Đang tính MD5 hash...")
        
        def get_md5(img_path):
            try:
                with open(img_path, 'rb') as f:
                    return hashlib.md5(f.read()).hexdigest()
            except:
                return None
        
        self.df['md5_hash'] = self.df['image_path'].apply(get_md5)
        print(f"✓ Đã tính MD5 hash cho {len(self.df)} images")
    
    def add_perceptual_hash(self):
        """
        Thêm Perceptual hash để phát hiện similar images
        Cần cài: pip install imagehash
        """
        if not HAS_IMAGEHASH:
            print("  Bỏ qua Perceptual hash (chưa cài imagehash)")
            return
        
        print("\n Đang tính Perceptual hash...")
        
        def get_phash(img_path):
            try:
                img = Image.open(img_path)
                return str(imagehash.average_hash(img))
            except:
                return None
        
        self.df['phash'] = self.df['image_path'].apply(get_phash)
        print(f"✓ Đã tính Perceptual hash cho {len(self.df)} images")
    
    def find_exact_duplicates(self):
        """
        Tìm ảnh trùng lặp hoàn toàn bằng MD5 hash
        """
        if 'md5_hash' not in self.df.columns:
            print("  Chưa có MD5 hash. Gọi add_md5_hash() trước.")
            return []
        
        print("\n Tìm exact duplicates (MD5)...")
        duplicates = self.df[self.df.duplicated(subset=['md5_hash'], keep=False)]
        
        if len(duplicates) == 0:
            print(" Không có ảnh trùng lặp")
        else:
            print(f"  Tìm thấy {len(duplicates)} ảnh trùng lặp:")
            for hash_val, group in duplicates.groupby('md5_hash'):
                print(f"  Hash {hash_val[:8]}...:")
                for _, row in group.iterrows():
                    print(f"    - {row['filename']}")
        
        return duplicates
    
    def find_similar_images(self, threshold=5):
        """
        Tìm ảnh tương tự bằng Perceptual hash
        threshold: 0-5 = rất tương tự, 6-10 = tương tự, 11+ = khác
        """
        if not HAS_IMAGEHASH or 'phash' not in self.df.columns:
            print("  Không thể tìm similar images (chưa có phash)")
            return []
        
        print(f"\n Tìm similar images (threshold={threshold})...")
        
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
            print(" Không có ảnh tương tự")
        else:
            print(f"  Tìm thấy {len(similar_groups)} nhóm ảnh tương tự:")
            for i, group in enumerate(similar_groups, 1):
                print(f"  Nhóm {i}:")
                for idx in group:
                    row = self.df.iloc[idx]
                    print(f"    - {row['filename']} ({row['width']}x{row['height']})")
        
        return similar_groups
    
    def analyze_data(self):
        """
        Phân tích dữ liệu theo workflow trong slide:
        - Đọc dữ liệu bằng pandas
        - Hiển thị thông tin bằng info(), describe()
        """
        if self.df is None:
            print("  Chưa có data, gọi create_metadata() trước")
            return
        
        print("\n" + "="*60)
        print(" THÔNG TIN DỮ LIỆU (df.info())")
        print("="*60)
        print(self.df.info())
        
        print("\n" + "="*60)
        print(" THỐNG KÊ MÔ TẢ (df.describe())")
        print("="*60)
        print(self.df.describe())
        
        print("\n" + "="*60)
        print(" PHÂN BỐ THEO CATEGORY")
        print("="*60)
        print(self.df['category'].value_counts())
    
    def check_missing_values(self):
        """Kiểm tra missing values"""
        print("\n" + "="*60)
        print(" KIỂM TRA MISSING VALUES")
        print("="*60)
        
        missing = self.df.isnull().sum()
        if missing.sum() == 0:
            print("✓ Không có missing values")
        else:
            print(missing[missing > 0])
    
    def detect_outliers(self):
        """
        Phát hiện outliers theo workflow:
        - Ảnh quá nhỏ hoặc quá lớn
        - Kích thước bất thường
        """
        print("\n" + "="*60)
        print(" PHÁT HIỆN OUTLIERS")
        print("="*60)
        
        # Tính IQR cho width và height
        Q1_width = self.df['width'].quantile(0.25)
        Q3_width = self.df['width'].quantile(0.75)
        IQR_width = Q3_width - Q1_width
        
        Q1_height = self.df['height'].quantile(0.25)
        Q3_height = self.df['height'].quantile(0.75)
        IQR_height = Q3_height - Q1_height
        
        # Outliers
        outliers_width = self.df[
            (self.df['width'] < Q1_width - 1.5 * IQR_width) |
            (self.df['width'] > Q3_width + 1.5 * IQR_width)
        ]
        
        outliers_height = self.df[
            (self.df['height'] < Q1_height - 1.5 * IQR_height) |
            (self.df['height'] > Q3_height + 1.5 * IQR_height)
        ]
        
        print(f" Width outliers: {len(outliers_width)}")
        print(f" Height outliers: {len(outliers_height)}")
        
        # Ảnh quá nhỏ (< 32x32)
        too_small = self.df[(self.df['width'] < 32) | (self.df['height'] < 32)]
        print(f"  Ảnh quá nhỏ (<32px): {len(too_small)}")
        
        return {
            'outliers_width': outliers_width,
            'outliers_height': outliers_height,
            'too_small': too_small
        }
    
    def clean_data(self, remove_outliers=False, min_size=32):
        """
        Làm sạch dữ liệu:
        - Loại bỏ duplicates
        - Loại bỏ ảnh quá nhỏ
        - Loại bỏ outliers (optional)
        """
        print("\n" + "="*60)
        print(" CLEANING DATA")
        print("="*60)
        
        original_size = len(self.df)
        
        # Remove duplicates by filename
        before_dup = len(self.df)
        self.df = self.df.drop_duplicates(subset=['filename'])
        print(f" Đã loại bỏ {before_dup - len(self.df)} duplicates (by filename)")
        
        # Remove exact duplicates by MD5 (nếu có)
        if 'md5_hash' in self.df.columns:
            before_md5 = len(self.df)
            self.df = self.df.drop_duplicates(subset=['md5_hash'], keep='first')
            removed_md5 = before_md5 - len(self.df)
            if removed_md5 > 0:
                print(f" Đã loại bỏ {removed_md5} exact duplicates (by MD5)")
        
        # Remove ảnh quá nhỏ
        before = len(self.df)
        self.df = self.df[
            (self.df['width'] >= min_size) & 
            (self.df['height'] >= min_size)
        ]
        print(f" Đã loại bỏ {before - len(self.df)} ảnh quá nhỏ")
        
        # Remove outliers nếu cần
        if remove_outliers:
            outliers = self.detect_outliers()
            outlier_indices = pd.concat([
                outliers['outliers_width'],
                outliers['outliers_height']
            ]).index.unique()
            
            before = len(self.df)
            self.df = self.df.drop(outlier_indices, errors='ignore')
            print(f" Đã loại bỏ {before - len(self.df)} outliers")
        
        print(f"\n Kết quả: {original_size} → {len(self.df)} images")
        return self.df
    
    def save_metadata(self):
        """Lưu metadata vào CSV"""
        metadata_file = Path('data/metadata.csv')
        self.df.to_csv(metadata_file, index=False)
        print(f"\n✓ Đã lưu metadata: {metadata_file}")
    
    def split_dataset(self, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        """
        Chia dataset thành train/val/test
        """
        from sklearn.model_selection import train_test_split
        
        print("\n" + "="*60)
        print(" CHIA DATASET")
        print("="*60)
        
        train_data = []
        val_data = []
        test_data = []
        
        for category in self.df['category'].unique():
            cat_df = self.df[self.df['category'] == category]
            
            # Split
            train, temp = train_test_split(cat_df, test_size=(val_ratio + test_ratio), random_state=42)
            val, test = train_test_split(temp, test_size=test_ratio/(val_ratio + test_ratio), random_state=42)
            
            train_data.append(train)
            val_data.append(val)
            test_data.append(test)
        
        self.train_df = pd.concat(train_data)
        self.val_df = pd.concat(val_data)
        self.test_df = pd.concat(test_data)
        
        print(f"✓ Train: {len(self.train_df)} ảnh ({train_ratio*100:.0f}%)")
        print(f"✓ Val:   {len(self.val_df)} ảnh ({val_ratio*100:.0f}%)")
        print(f"✓ Test:  {len(self.test_df)} ảnh ({test_ratio*100:.0f}%)")
    
    def resize_and_save(self, target_size=(64, 64), output_dir='data/processed'):
        """
        Resize ảnh và lưu vào thư mục processed
        """
        from PIL import Image
        import shutil
        
        print("\n" + "="*60)
        print("  RESIZE VÀ LƯU ẢNH")
        print("="*60)
        
        output_path = Path(output_dir)
        
        # Tạo thư mục
        for split in ['train', 'val', 'test']:
            for category in self.df['category'].unique():
                (output_path / split / category).mkdir(parents=True, exist_ok=True)
        
        # Process từng split
        for split_name, split_df in [('train', self.train_df), ('val', self.val_df), ('test', self.test_df)]:
            print(f"\n  Đang xử lý {split_name} set...")
            count = 0
            
            for _, row in split_df.iterrows():
                try:
                    img = Image.open(row['image_path'])
                    img_resized = img.resize(target_size, Image.Resampling.LANCZOS)
                    
                    if img_resized.mode != 'RGB':
                        img_resized = img_resized.convert('RGB')
                    
                    save_path = output_path / split_name / row['category'] / row['filename']
                    img_resized.save(save_path, 'PNG')
                    count += 1
                except:
                    continue
            
            print(f"✓ Đã xử lý {count}/{len(split_df)} ảnh")
        
        print(f"\n✓ Đã lưu tất cả ảnh vào: {output_path}")


def main():
    """Main function - Chạy toàn bộ pipeline"""
    print("Lam sach du lieu + Xu ly anh")
    print("="*70)
    
    cleaner = DataCleaner()
    
    # Part 1: Data Cleaning
    cleaner.create_metadata()
    cleaner.add_md5_hash()
    cleaner.add_perceptual_hash()
    cleaner.find_exact_duplicates()
    cleaner.find_similar_images(threshold=5)
    cleaner.analyze_data()
    cleaner.check_missing_values()
    cleaner.detect_outliers()
    cleaner.clean_data(remove_outliers=False)
    cleaner.save_metadata()
    
    # Part 2: Image Processing
    cleaner.split_dataset(train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
    cleaner.resize_and_save(target_size=(64, 64))
    
    print("\n" + "="*70)
    print("HOAN TAT!")
    print("="*70)
    print(f"Tong so anh: {len(cleaner.df)}")
    print(f"Metadata: data/metadata.csv")
    print(f"Processed: data/processed/")
    print(f"   - Train: {len(cleaner.train_df)} anh")
    print(f"   - Val:   {len(cleaner.val_df)} anh")
    print(f"   - Test:  {len(cleaner.test_df)} anh")


if __name__ == '__main__':
    main()
