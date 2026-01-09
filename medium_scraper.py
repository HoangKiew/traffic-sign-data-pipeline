"""
MEDIUM SCRAPER - Thu thập 1000-2000 ảnh trong 1-2 giờ
Cân bằng giữa số lượng và thời gian
"""

import time
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import hashlib


class MediumScraper:
    """Scraper để thu thập 1-2k ảnh trong 1-2 giờ"""
    
    def __init__(self):
        self.output_dir = Path('data/raw')
        self.downloaded_urls = set()
        self.downloaded_hashes = set()
        self.total_downloaded = 0
        
        # Setup Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✓ Selenium khởi động thành công")
        except:
            print("⚠️  Selenium không khả dụng")
            self.driver = None
    
    def download_and_save(self, url, category):
        """Download và lưu ảnh"""
        if url in self.downloaded_urls:
            return False
        
        try:
            response = requests.get(url, timeout=10)
            img_data = Image.open(BytesIO(response.content))
            
            if img_data.width < 80 or img_data.height < 80:
                return False
            
            # Check hash
            img_hash = hashlib.md5(response.content).hexdigest()
            if img_hash in self.downloaded_hashes:
                return False
            
            if img_data.mode != 'RGB':
                img_data = img_data.convert('RGB')
            
            category_dir = self.output_dir / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = int(time.time() * 1000)
            filename = f"{category}_{self.total_downloaded}_{timestamp}.jpg"
            filepath = category_dir / filename
            
            img_data.save(filepath, 'JPEG', quality=95)
            
            self.downloaded_urls.add(url)
            self.downloaded_hashes.add(img_hash)
            self.total_downloaded += 1
            
            if self.total_downloaded % 100 == 0:
                print(f"  ✓ Progress: {self.total_downloaded} ảnh")
            
            return True
        except:
            return False
    
    def scrape_google_images(self, query, category, target=150):
        """Scrape Google Images - Tối ưu tốc độ"""
        if not self.driver:
            return 0
        
        print(f"\n{query}")
        
        search_url = f"https://www.google.com/search?q={query}&tbm=isch"
        self.driver.get(search_url)
        time.sleep(1)
        
        count = 0
        scroll_count = 0
        max_scrolls = 8
        
        while count < target and scroll_count < max_scrolls:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            scroll_count += 1
            
            images = self.driver.find_elements(By.TAG_NAME, "img")
            
            for img in images:
                if count >= target:
                    break
                
                try:
                    src = img.get_attribute('src')
                    if src and 'http' in src and not src.startswith('data:'):
                        if self.download_and_save(src, category):
                            count += 1
                except:
                    continue
        
        print(f"  -> {count} anh")
        return count
    
    def close(self):
        if self.driver:
            self.driver.quit()


def main():
    """Main - Thu thập 1-2k ảnh"""
    print("SCRAPING...")
    
    scraper = MediumScraper()
    
    queries = [
        # Prohibitory - 6 queries
        ("bien cam giao thong viet nam", "prohibitory", 150),
        ("bien cam duong bo", "prohibitory", 150),
        ("prohibitory traffic signs vietnam", "prohibitory", 150),
        ("bien cam do xe", "prohibitory", 100),
        ("bien cam re", "prohibitory", 100),
        ("no entry sign vietnam", "prohibitory", 100),
        
        # Warning - 6 queries
        ("bien canh bao giao thong viet nam", "warning", 150),
        ("bien bao nguy hiem duong bo", "warning", 150),
        ("warning traffic signs vietnam", "warning", 150),
        ("bien canh bao duong xau", "warning", 100),
        ("bien canh bao nga tu", "warning", 100),
        ("road warning signs vietnam", "warning", 100),
        
        # Mandatory - 6 queries
        ("bien hieu lenh giao thong viet nam", "mandatory", 150),
        ("bien bao bat buoc duong bo", "mandatory", 150),
        ("mandatory traffic signs vietnam", "mandatory", 150),
        ("bien hieu lenh re", "mandatory", 100),
        ("bien bao huong di", "mandatory", 100),
        ("regulatory signs vietnam", "mandatory", 100),
        
        # Informative - 6 queries
        ("bien chi dan giao thong viet nam", "informative", 150),
        ("bien bao chi duong", "informative", 150),
        ("information signs vietnam", "informative", 150),
        ("bien chi dan dia danh", "informative", 100),
        ("bien bao huong dan", "informative", 100),
        ("guide signs vietnam", "informative", 100),
    ]
    
    for query, category, target in queries:
        scraper.scrape_google_images(query, category, target)
        time.sleep(5)  # Delay ngắn giữa queries
    
    scraper.close()
    
    print("\n" + "="*70)
    print("HOAN TAT!")
    print("="*70)
    print(f"Tong so anh: {scraper.total_downloaded}")
    
    for category in ['prohibitory', 'warning', 'mandatory', 'informative']:
        category_dir = Path('data/raw') / category
        if category_dir.exists():
            count = len(list(category_dir.glob('*.jpg')))
            print(f"  {category:15s}: {count:4d} anh")


if __name__ == '__main__':
    main()
