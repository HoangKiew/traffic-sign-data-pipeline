"""
Data Cleaning Module
Xử lý và làm sạch dữ liệu theo workflow trong slide
"""

import pandas as pd
import numpy as np
from pathlib import Path
from PIL import Image
import os


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
        print("📊 Đang tạo metadata từ raw images...")
        
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
    
    def analyze_data(self):
        """
        Phân tích dữ liệu theo workflow trong slide:
        - Đọc dữ liệu bằng pandas
        - Hiển thị thông tin bằng info(), describe()
        """
        if self.df is None:
            print("⚠️  Chưa có data, gọi create_metadata() trước")
            return
        
        print("\n" + "="*60)
        print("📋 THÔNG TIN DỮ LIỆU (df.info())")
        print("="*60)
        print(self.df.info())
        
        print("\n" + "="*60)
        print("📊 THỐNG KÊ MÔ TẢ (df.describe())")
        print("="*60)
        print(self.df.describe())
        
        print("\n" + "="*60)
        print("📈 PHÂN BỐ THEO CATEGORY")
        print("="*60)
        print(self.df['category'].value_counts())
    
    def check_missing_values(self):
        """Kiểm tra missing values"""
        print("\n" + "="*60)
        print("🔍 KIỂM TRA MISSING VALUES")
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
        print("🎯 PHÁT HIỆN OUTLIERS")
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
        
        print(f"📏 Width outliers: {len(outliers_width)}")
        print(f"📏 Height outliers: {len(outliers_height)}")
        
        # Ảnh quá nhỏ (< 32x32)
        too_small = self.df[(self.df['width'] < 32) | (self.df['height'] < 32)]
        print(f"⚠️  Ảnh quá nhỏ (<32px): {len(too_small)}")
        
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
        print("🧹 CLEANING DATA")
        print("="*60)
        
        original_size = len(self.df)
        
        # Remove duplicates
        self.df = self.df.drop_duplicates(subset=['filename'])
        print(f"✓ Đã loại bỏ {original_size - len(self.df)} duplicates")
        
        # Remove ảnh quá nhỏ
        before = len(self.df)
        self.df = self.df[
            (self.df['width'] >= min_size) & 
            (self.df['height'] >= min_size)
        ]
        print(f"✓ Đã loại bỏ {before - len(self.df)} ảnh quá nhỏ")
        
        # Remove outliers nếu cần
        if remove_outliers:
            outliers = self.detect_outliers()
            outlier_indices = pd.concat([
                outliers['outliers_width'],
                outliers['outliers_height']
            ]).index.unique()
            
            before = len(self.df)
            self.df = self.df.drop(outlier_indices, errors='ignore')
            print(f"✓ Đã loại bỏ {before - len(self.df)} outliers")
        
        print(f"\n📊 Kết quả: {original_size} → {len(self.df)} images")
        return self.df
    
    def save_metadata(self, output_path='data/metadata.csv'):
        """Lưu metadata đã clean"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.df.to_csv(output_path, index=False)
        print(f"\n✓ Đã lưu metadata vào {output_path}")


def main():
    """Main function"""
    print("🚀 Data Cleaning Pipeline")
    print("="*60)
    
    cleaner = DataCleaner()
    
    # Step 1: Tạo metadata
    cleaner.create_metadata()
    
    # Step 2: Phân tích dữ liệu (theo slide)
    cleaner.analyze_data()
    
    # Step 3: Kiểm tra missing values
    cleaner.check_missing_values()
    
    # Step 4: Phát hiện outliers
    cleaner.detect_outliers()
    
    # Step 5: Clean data
    cleaner.clean_data(remove_outliers=False, min_size=32)
    
    # Step 6: Lưu metadata
    cleaner.save_metadata()
    
    print("\n" + "="*60)
    print("✅ Hoàn tất Data Cleaning!")
    print("="*60)


if __name__ == '__main__':
    main()
