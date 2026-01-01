"""
Advanced Web Scraper sử dụng Selenium
Dùng để scrape các trang web động (JavaScript-heavy)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from pathlib import Path
import requests
from PIL import Image
from io import BytesIO
import json


class SeleniumScraper:
    """Scraper sử dụng Selenium cho dynamic websites"""
    
    def __init__(self, output_dir='data/raw', headless=True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = None
        self.chrome_options = chrome_options
        self.metadata = []
    
    def start_driver(self):
        """Khởi động Chrome driver"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            print("✓ Đã khởi động Chrome driver")
        except Exception as e:
            print(f"❌ Lỗi khởi động driver: {e}")
            print("\n💡 Cần cài ChromeDriver:")
            print("   1. Download: https://chromedriver.chromium.org/")
            print("   2. Hoặc dùng: pip install webdriver-manager")
            raise
    
    def close_driver(self):
        """Đóng driver"""
        if self.driver:
            self.driver.quit()
            print("✓ Đã đóng Chrome driver")
    
    def scrape_google_images_advanced(self, query, category, max_images=100):
        """
        Scrape Google Images với Selenium (scroll để load thêm ảnh)
        """
        print(f"\n🔍 Scrape Google Images: '{query}'")
        
        if not self.driver:
            self.start_driver()
        
        # Mở Google Images
        search_url = f"https://www.google.com/search?q={query}&tbm=isch"
        self.driver.get(search_url)
        time.sleep(2)
        
        # Scroll để load thêm ảnh
        print("📜 Đang scroll để load ảnh...")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(5):  # Scroll 5 lần
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Tìm tất cả ảnh
        print("🖼️  Đang thu thập URLs...")
        img_elements = self.driver.find_elements(By.TAG_NAME, "img")
        
        urls = []
        for img in img_elements:
            try:
                src = img.get_attribute('src')
                if src and not src.startswith('data:') and 'http' in src:
                    urls.append(src)
            except:
                continue
        
        print(f"✓ Tìm thấy {len(urls)} URLs")
        
        # Download ảnh
        count = 0
        for i, url in enumerate(urls[:max_images]):
            try:
                filename = f"{category}_google_{int(time.time())}_{i}.jpg"
                save_path = self.output_dir / category / filename
                
                if self.download_image(url, save_path):
                    self.metadata.append({
                        'filename': filename,
                        'category': category,
                        'source': 'google_images_selenium',
                        'query': query,
                        'url': url
                    })
                    count += 1
                    print(f"  [{count}/{max_images}] ✓ {filename}")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ⚠️  Lỗi: {e}")
                continue
        
        print(f"\n✓ Đã download {count} ảnh")
        return count
    
    def download_image(self, url, save_path, timeout=10):
        """Download ảnh từ URL"""
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content))
            
            # Filter ảnh quá nhỏ
            if img.width < 100 or img.height < 100:
                return False
            
            # Convert to RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save
            save_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(save_path, 'JPEG', quality=95)
            return True
            
        except Exception as e:
            return False
    
    def save_metadata(self):
        """Lưu metadata"""
        metadata_file = self.output_dir / 'selenium_scraping_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Đã lưu metadata: {metadata_file}")


def main():
    """Main function"""
    print("🚀 Selenium Web Scraper cho Biển báo Giao thông")
    print("="*60)
    
    scraper = SeleniumScraper(headless=False)  # headless=False để xem browser
    
    try:
        scraper.start_driver()
        
        # Ví dụ: Scrape biển cấm
        queries = [
            ('biển cấm đường Việt Nam', 'prohibitory'),
            ('biển cảnh báo giao thông Việt Nam', 'warning'),
            ('biển hiệu lệnh giao thông', 'mandatory'),
            ('biển chỉ dẫn đường', 'informative')
        ]
        
        print("\n💡 Sẵn sàng scrape! Bạn có thể:")
        print("   1. Chạy từng query:")
        print("      scraper.scrape_google_images_advanced('biển cấm', 'prohibitory', 50)")
        print("\n   2. Hoặc uncomment code dưới để chạy tất cả:\n")
        
        # Uncomment để chạy
        # for query, category in queries:
        #     scraper.scrape_google_images_advanced(query, category, max_images=30)
        #     time.sleep(5)
        
        # scraper.save_metadata()
        
    finally:
        scraper.close_driver()
    
    print("\n✅ Hoàn tất!")


if __name__ == '__main__':
    main()
