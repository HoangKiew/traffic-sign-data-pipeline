"""
Interactive Scraper - Bạn mở trang, mình cào ảnh
Nhập URL trang web, script sẽ tự động cào tất cả ảnh
"""

import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
from urllib.parse import urljoin, urlparse
from PIL import Image
from io import BytesIO
import json


class InteractiveScraper:
    """Scraper tương tác - bạn cho URL, mình cào ảnh"""
    
    def __init__(self, output_dir='data/raw'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Categories
        self.categories = ['prohibitory', 'warning', 'mandatory', 'informative']
        for cat in self.categories:
            (self.output_dir / cat).mkdir(exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        self.downloaded_count = 0
    
    def download_image(self, url, category, index):
        """Download một ảnh"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Validate
            img = Image.open(BytesIO(response.content))
            
            # Filter nhỏ
            if img.width < 50 or img.height < 50:
                return False
            
            # Convert RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save
            timestamp = int(time.time() * 1000)
            filename = f"{category}_{index}_{timestamp}.jpg"
            save_path = self.output_dir / category / filename
            
            img.save(save_path, 'JPEG', quality=95)
            print(f"  ✓ {filename} ({img.width}x{img.height})")
            return True
            
        except Exception as e:
            print(f"  ⚠️  Lỗi: {str(e)[:40]}")
            return False
    
    def scrape_page(self, url, category='informative'):
        """Cào tất cả ảnh từ một trang"""
        print(f"\n{'='*70}")
        print(f"🌐 ĐANG CÀO: {url}")
        print(f"📂 Category: {category}")
        print(f"{'='*70}\n")
        
        try:
            # Get page
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm tất cả ảnh
            images = soup.find_all('img')
            print(f"🔍 Tìm thấy {len(images)} thẻ <img>\n")
            
            count = 0
            for i, img in enumerate(images, 1):
                # Lấy src
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if not src:
                    continue
                
                # Convert to absolute URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(url, src)
                elif not src.startswith('http'):
                    src = urljoin(url, src)
                
                # Skip data URLs
                if src.startswith('data:'):
                    continue
                
                # Download
                if self.download_image(src, category, i):
                    count += 1
                    self.downloaded_count += 1
                
                time.sleep(2.0)  # Tăng delay lên 2s để tránh rate limit
            
            print(f"\n✅ Đã cào {count}/{len(images)} ảnh từ trang này")
            return count
            
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return 0
    
    def interactive_mode(self):
        """Chế độ tương tác"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║          🎯 INTERACTIVE IMAGE SCRAPER                        ║
║          Bạn cho URL, mình cào ảnh!                          ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        print("📋 CATEGORIES:")
        for i, cat in enumerate(self.categories, 1):
            print(f"   {i}. {cat}")
        
        print("\n💡 HƯỚNG DẪN:")
        print("   - Nhập URL trang web muốn cào")
        print("   - Chọn category (1-4)")
        print("   - Gõ 'quit' để thoát")
        print("   - Gõ 'stats' để xem thống kê\n")
        
        while True:
            print("─" * 70)
            url = input("\n🔗 Nhập URL (hoặc 'quit'/'stats'): ").strip()
            
            if url.lower() == 'quit':
                break
            
            if url.lower() == 'stats':
                self.show_stats()
                continue
            
            if not url.startswith('http'):
                print("❌ URL không hợp lệ! Phải bắt đầu bằng http:// hoặc https://")
                continue
            
            # Chọn category
            cat_input = input("📂 Chọn category (1-4, Enter=4): ").strip()
            if not cat_input:
                cat_input = '4'
            
            try:
                cat_index = int(cat_input) - 1
                if 0 <= cat_index < len(self.categories):
                    category = self.categories[cat_index]
                else:
                    category = 'informative'
            except:
                category = 'informative'
            
            # Scrape
            self.scrape_page(url, category)
        
        print("\n" + "="*70)
        print("👋 Tạm biệt!")
        self.show_stats()
    
    def show_stats(self):
        """Hiển thị thống kê"""
        print("\n" + "="*70)
        print("📊 THỐNG KÊ")
        print("="*70)
        
        total = 0
        for cat in self.categories:
            count = len(list((self.output_dir / cat).glob('*.jpg')))
            total += count
            print(f"   {cat:15s}: {count:3d} ảnh")
        
        print(f"\n   {'TỔNG':15s}: {total:3d} ảnh")
        print("="*70)


def main():
    """Main function"""
    scraper = InteractiveScraper()
    scraper.interactive_mode()


if __name__ == '__main__':
    main()
