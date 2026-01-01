"""
Data Collection Module - Traffic Sign Dataset Downloader
Tải dataset biển báo giao thông từ các nguồn công khai
"""

import os
import requests
import zipfile
from pathlib import Path
from tqdm import tqdm


class DatasetDownloader:
    """Download public traffic sign datasets"""
    
    def __init__(self, data_dir='data/raw'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def download_file(self, url, filename):
        """Download file với progress bar"""
        filepath = self.data_dir / filename
        
        if filepath.exists():
            print(f"✓ {filename} đã tồn tại, bỏ qua download")
            return filepath
        
        print(f"📥 Đang tải {filename}...")
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filepath, 'wb') as file, tqdm(
            desc=filename,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                progress_bar.update(size)
        
        print(f"✓ Đã tải xong {filename}")
        return filepath
    
    def extract_zip(self, zip_path, extract_to=None):
        """Giải nén file zip"""
        if extract_to is None:
            extract_to = self.data_dir
        
        print(f"📦 Đang giải nén {zip_path.name}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"✓ Đã giải nén xong")
    
    def download_gtsrb(self):
        """
        Download GTSRB (German Traffic Sign Recognition Benchmark)
        Dataset công khai phổ biến nhất cho traffic sign classification
        """
        print("\n" + "="*60)
        print("📊 GTSRB Dataset (German Traffic Sign Recognition Benchmark)")
        print("="*60)
        
        # Note: URL thực tế có thể thay đổi, cần update
        # Đây là ví dụ structure, bạn cần tìm URL chính xác
        urls = {
            'train': 'https://sid.erda.dk/public/archives/daaeac0d7ce1152aea9b61d9f1e19370/GTSRB_Final_Training_Images.zip',
            'test': 'https://sid.erda.dk/public/archives/daaeac0d7ce1152aea9b61d9f1e19370/GTSRB_Final_Test_Images.zip'
        }
        
        print("\n⚠️  Lưu ý: Bạn cần download dataset từ Kaggle hoặc nguồn chính thức:")
        print("   🔗 Kaggle: https://www.kaggle.com/datasets/meowmeowmeowmeowmeow/gtsrb-german-traffic-sign")
        print("   🔗 Official: https://benchmark.ini.rub.de/")
        print("\nHoặc sử dụng Kaggle API:")
        print("   kaggle datasets download -d meowmeowmeowmeowmeow/gtsrb-german-traffic-sign")
        
        return self.data_dir
    
    def download_sample_dataset(self):
        """
        Tạo sample dataset nhỏ để test pipeline
        """
        print("\n" + "="*60)
        print("🧪 Tạo Sample Dataset để test")
        print("="*60)
        
        # Tạo cấu trúc thư mục mẫu
        categories = ['prohibitory', 'warning', 'mandatory', 'informative']
        
        for category in categories:
            category_path = self.data_dir / category
            category_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Đã tạo thư mục: {category}")
        
        print("\n💡 Tip: Bạn có thể:")
        print("   1. Tự download ảnh từ Google Images")
        print("   2. Sử dụng web scraper (scraper.py)")
        print("   3. Download dataset từ Kaggle")
        
        return self.data_dir


def main():
    """Main function"""
    print("🚀 Traffic Sign Dataset Downloader")
    print("="*60)
    
    downloader = DatasetDownloader()
    
    # Tạo sample structure
    downloader.download_sample_dataset()
    
    # Hướng dẫn download GTSRB
    downloader.download_gtsrb()
    
    print("\n" + "="*60)
    print("✅ Hoàn tất! Kiểm tra thư mục data/raw/")
    print("="*60)


if __name__ == '__main__':
    main()
