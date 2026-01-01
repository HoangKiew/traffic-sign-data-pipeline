"""
Image Preprocessing Module
Xử lý ảnh trước khi training model
"""

import numpy as np
import pandas as pd
from pathlib import Path
from PIL import Image
import shutil
from sklearn.model_selection import train_test_split
from tqdm import tqdm


class ImagePreprocessor:
    """Preprocess images for model training"""
    
    def __init__(self, metadata_path='data/metadata.csv', 
                 output_dir='data/processed', 
                 target_size=(64, 64)):
        self.df = pd.read_csv(metadata_path)
        self.output_dir = Path(output_dir)
        self.target_size = target_size
        
        # Tạo thư mục output
        for split in ['train', 'val', 'test']:
            (self.output_dir / split).mkdir(parents=True, exist_ok=True)
    
    def resize_and_save(self, img_path, output_path):
        """Resize ảnh và lưu"""
        try:
            with Image.open(img_path) as img:
                # Convert to RGB nếu cần
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize
                img_resized = img.resize(self.target_size, Image.Resampling.LANCZOS)
                
                # Save
                img_resized.save(output_path, 'PNG')
                return True
        except Exception as e:
            print(f"⚠️  Lỗi xử lý {img_path}: {e}")
            return False
    
    def split_dataset(self):
        """
        Chia dataset thành train/val/test
        Xử lý đặc biệt cho categories có ít ảnh
        """
        print("\n📊 Chia dataset...")
        
        # Kiểm tra số lượng ảnh mỗi category
        print("\n📋 Phân bố category:")
        for category in self.df['category'].unique():
            count = len(self.df[self.df['category'] == category])
            print(f"  {category:15s}: {count:3d} ảnh")
        
        # Split theo category để đảm bảo balanced
        train_data = []
        val_data = []
        test_data = []
        
        for category in self.df['category'].unique():
            category_df = self.df[self.df['category'] == category]
            n_samples = len(category_df)
            
            # Nếu category có ít hơn 6 ảnh, bỏ hết vào train
            if n_samples < 6:
                print(f"  ⚠️  {category}: {n_samples} ảnh → Tất cả vào train")
                train_data.append(category_df)
                continue
            
            # Nếu có từ 6-15 ảnh, chia đơn giản: 80% train, 20% test (không có val)
            if n_samples < 15:
                print(f"  ⚠️  {category}: {n_samples} ảnh → Train/Test (80/20)")
                train, test = train_test_split(
                    category_df,
                    test_size=0.2,
                    random_state=42
                )
                train_data.append(train)
                test_data.append(test)
                continue
            
            # Nếu đủ ảnh (>=15), chia bình thường train/val/test (70/15/15)
            print(f"  ✓ {category}: {n_samples} ảnh → Train/Val/Test (70/15/15)")
            
            # Train vs (Val + Test)
            train, temp = train_test_split(
                category_df, 
                test_size=0.3,  # 30% cho val+test
                random_state=42
            )
            
            # Val vs Test
            val, test = train_test_split(
                temp,
                test_size=0.5,  # Chia đôi 30% → 15% val, 15% test
                random_state=42
            )
            
            train_data.append(train)
            val_data.append(val)
            test_data.append(test)
        
        # Combine
        train_df = pd.concat(train_data, ignore_index=True) if train_data else pd.DataFrame()
        val_df = pd.concat(val_data, ignore_index=True) if val_data else pd.DataFrame()
        test_df = pd.concat(test_data, ignore_index=True) if test_data else pd.DataFrame()
        
        print(f"\n✓ Kết quả split:")
        print(f"  Train: {len(train_df):3d} images ({len(train_df)/len(self.df)*100:.1f}%)")
        print(f"  Val:   {len(val_df):3d} images ({len(val_df)/len(self.df)*100:.1f}%)")
        print(f"  Test:  {len(test_df):3d} images ({len(test_df)/len(self.df)*100:.1f}%)")
        
        return train_df, val_df, test_df
    
    def process_split(self, df, split_name):
        """Process một split (train/val/test)"""
        if len(df) == 0:
            print(f"\n⚠️  {split_name} set trống, bỏ qua...")
            return
        
        print(f"\n🔄 Đang xử lý {split_name} set...")
        
        success_count = 0
        
        for idx, row in tqdm(df.iterrows(), total=len(df), desc=f"Processing {split_name}"):
            category = row['category']
            img_path = Path(row['image_path'])
            
            # Tạo thư mục category
            category_dir = self.output_dir / split_name / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # Output path
            output_path = category_dir / f"{img_path.stem}.png"
            
            # Resize và save
            if self.resize_and_save(img_path, output_path):
                success_count += 1
        
        print(f"✓ Đã xử lý {success_count}/{len(df)} images cho {split_name}")
    
    def preprocess_all(self):
        """Preprocess toàn bộ dataset"""
        print("🚀 Bắt đầu preprocessing...")
        print(f"  Target size: {self.target_size}")
        print(f"  Output dir: {self.output_dir}")
        print(f"  Total images: {len(self.df)}")
        
        # Split dataset
        train_df, val_df, test_df = self.split_dataset()
        
        # Process từng split
        self.process_split(train_df, 'train')
        self.process_split(val_df, 'val')
        self.process_split(test_df, 'test')
        
        # Save split info
        split_info = {
            'train': len(train_df),
            'val': len(val_df),
            'test': len(test_df),
            'target_size': self.target_size
        }
        
        print("\n" + "="*60)
        print("✅ Hoàn tất preprocessing!")
        print("="*60)
        print(f"📁 Processed data: {self.output_dir}")
        print(f"\n📊 Tổng kết:")
        print(f"  - Train: {len(train_df)} images")
        print(f"  - Val:   {len(val_df)} images")
        print(f"  - Test:  {len(test_df)} images")
        print(f"  - Total: {len(train_df) + len(val_df) + len(test_df)} images")
        
        return split_info


def main():
    """Main function"""
    print("🚀 Image Preprocessing Pipeline")
    print("="*60)
    
    preprocessor = ImagePreprocessor(target_size=(64, 64))
    preprocessor.preprocess_all()


if __name__ == '__main__':
    main()
