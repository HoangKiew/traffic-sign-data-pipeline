"""
Web Scraper cho Biển báo Giao thông
Thu thập dữ liệu THÔ từ web (không dùng dataset có sẵn)
"""

import os
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
from urllib.parse import urljoin, urlparse
from PIL import Image
from io import BytesIO
import json


class TrafficSignScraper:
    """Scrape traffic sign images from web sources"""
    
    def __init__(self, output_dir='data/raw'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Categories
        self.categories = {
            'prohibitory': 'Biển cấm',
            'warning': 'Biển cảnh báo', 
            'mandatory': 'Biển hiệu lệnh',
            'informative': 'Biển chỉ dẫn'
        }
        
        # Create category folders
        for category in self.categories.keys():
            (self.output_dir / category).mkdir(exist_ok=True)
        
        # Headers để tránh bị block
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Metadata
        self.metadata = []
    
    def download_image(self, url, save_path, timeout=10):
        """Download một ảnh từ URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            
            # Kiểm tra xem có phải ảnh không
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type:
                print(f"⚠️  Không phải ảnh: {url}")
                return False
            
            # Mở và validate ảnh
            img = Image.open(BytesIO(response.content))
            
            # Chỉ lưu ảnh đủ lớn (tránh icon nhỏ)
            if img.width < 50 or img.height < 50:
                print(f"⚠️  Ảnh quá nhỏ ({img.width}x{img.height}): {url}")
                return False
            
            # Convert to RGB nếu cần
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Lưu ảnh
            img.save(save_path, 'JPEG', quality=95)
            print(f"✓ Đã lưu: {save_path.name}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi download {url}: {e}")
            return False
    
    def scrape_google_images(self, query, category, max_images=50):
        """
        Scrape từ Google Images
        Note: Google Images khó scrape, cần dùng API hoặc Selenium
        Đây là ví dụ cơ bản
        """
        print(f"\n🔍 Tìm kiếm: '{query}' (category: {category})")
        
        # Google Images search URL
        search_url = f"https://www.google.com/search?q={query}&tbm=isch"
        
        try:
            response = requests.get(search_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm các thẻ img
            img_tags = soup.find_all('img')
            
            count = 0
            for img in img_tags[:max_images]:
                if count >= max_images:
                    break
                
                img_url = img.get('src') or img.get('data-src')
                if not img_url or img_url.startswith('data:'):
                    continue
                
                # Tạo filename
                filename = f"{category}_{int(time.time())}_{count}.jpg"
                save_path = self.output_dir / category / filename
                
                # Download
                if self.download_image(img_url, save_path):
                    self.metadata.append({
                        'filename': filename,
                        'category': category,
                        'source': 'google_images',
                        'query': query,
                        'url': img_url
                    })
                    count += 1
                
                time.sleep(0.5)  # Delay để tránh bị block
            
            print(f"✓ Đã scrape {count} ảnh cho '{query}'")
            return count
            
        except Exception as e:
            print(f"❌ Lỗi scrape Google Images: {e}")
            return 0
    
    def scrape_from_url_list(self, url_list_file, category):
        """
        Scrape từ danh sách URLs có sẵn
        Format file: mỗi dòng là một URL ảnh
        """
        print(f"\n📋 Scrape từ file: {url_list_file}")
        
        if not Path(url_list_file).exists():
            print(f"❌ File không tồn tại: {url_list_file}")
            return 0
        
        with open(url_list_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        count = 0
        for i, url in enumerate(urls):
            filename = f"{category}_{int(time.time())}_{i}.jpg"
            save_path = self.output_dir / category / filename
            
            if self.download_image(url, save_path):
                self.metadata.append({
                    'filename': filename,
                    'category': category,
                    'source': 'url_list',
                    'url': url
                })
                count += 1
            
            time.sleep(0.3)
        
        print(f"✓ Đã download {count}/{len(urls)} ảnh")
        return count
    
    def scrape_website(self, base_url, category, max_pages=5):
        """
        Scrape tất cả ảnh từ một website
        Tìm tất cả thẻ <img> trong trang
        """
        print(f"\n🌐 Scrape website: {base_url}")
        
        try:
            response = requests.get(base_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm tất cả ảnh
            img_tags = soup.find_all('img')
            
            count = 0
            for i, img in enumerate(img_tags):
                img_url = img.get('src') or img.get('data-src')
                if not img_url:
                    continue
                
                # Convert relative URL to absolute
                img_url = urljoin(base_url, img_url)
                
                # Skip data URLs
                if img_url.startswith('data:'):
                    continue
                
                filename = f"{category}_{int(time.time())}_{i}.jpg"
                save_path = self.output_dir / category / filename
                
                if self.download_image(img_url, save_path):
                    self.metadata.append({
                        'filename': filename,
                        'category': category,
                        'source': base_url,
                        'url': img_url
                    })
                    count += 1
                
                time.sleep(0.5)
            
            print(f"✓ Đã scrape {count} ảnh từ {base_url}")
            return count
            
        except Exception as e:
            print(f"❌ Lỗi scrape website: {e}")
            return 0
    
    def save_metadata(self):
        """Lưu metadata"""
        metadata_file = self.output_dir / 'scraping_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Đã lưu metadata: {metadata_file}")
    
    def get_statistics(self):
        """Thống kê dữ liệu đã scrape"""
        stats = {}
        for category in self.categories.keys():
            category_dir = self.output_dir / category
            count = len(list(category_dir.glob('*.jpg')))
            stats[category] = count
        return stats


def main():
    """Main function - Ví dụ sử dụng"""
    print("🚀 Traffic Sign Web Scraper")
    print("="*60)
    
    scraper = TrafficSignScraper()
    
    print("\n💡 HƯỚNG DẪN SỬ DỤNG:")
    print("-"*60)
    print("""
    Có 3 cách thu thập dữ liệu thô:
    
    1. SCRAPE TỪ GOOGLE IMAGES (cơ bản, có thể bị giới hạn):
       scraper.scrape_google_images('biển cấm đường', 'prohibitory', max_images=50)
    
    2. SCRAPE TỪ FILE DANH SÁCH URLs:
       - Tạo file .txt với mỗi dòng là 1 URL ảnh
       - Gọi: scraper.scrape_from_url_list('urls.txt', 'warning')
    
    3. SCRAPE TỪ WEBSITE CỤ THỂ:
       scraper.scrape_website('https://example.com/traffic-signs', 'mandatory')
    
    Sau khi scrape xong, gọi:
       scraper.save_metadata()
    """)
    
    # Ví dụ: Scrape một số ảnh test
    print("\n🧪 DEMO: Scrape một số ảnh test...")
    
    # Tạo file URLs mẫu nếu chưa có
    sample_urls_file = Path('sample_urls.txt')
    if not sample_urls_file.exists():
        print("\n💡 Tạo file 'sample_urls.txt' và thêm URLs ảnh biển báo vào đó")
        print("   Mỗi dòng một URL, ví dụ:")
        print("   https://example.com/image1.jpg")
        print("   https://example.com/image2.jpg")
    
    # Statistics
    print("\n📊 THỐNG KÊ HIỆN TẠI:")
    stats = scraper.get_statistics()
    total = sum(stats.values())
    print(f"  Tổng số ảnh: {total}")
    for category, count in stats.items():
        print(f"  - {scraper.categories[category]}: {count} ảnh")
    
    print("\n" + "="*60)
    print("✅ Sẵn sàng scrape dữ liệu!")
    print("="*60)


if __name__ == '__main__':
    main()
