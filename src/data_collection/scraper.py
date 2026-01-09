import os
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
from urllib.parse import urljoin, urlparse
from PIL import Image
from io import BytesIO
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TrafficSignScraper:
    
    def __init__(self, output_dir='data/raw'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Các loại biển báo
        self.categories = {
            'prohibitory': 'Biển cấm',
            'warning': 'Biển cảnh báo', 
            'mandatory': 'Biển hiệu lệnh',
            'informative': 'Biển chỉ dẫn'
        }
        
        # Tạo thư mục cho từng category
        for category in self.categories.keys():
            (self.output_dir / category).mkdir(exist_ok=True)
        
        # Header tránh bị block
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        self.metadata = []
    
    def download_image(self, url, save_path, timeout=10):
        # Tải và kiểm tra ảnh
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            
            if 'image' not in response.headers.get('content-type', ''):
                print(f"Không phải ảnh: {url}")
                return False
            
            img = Image.open(BytesIO(response.content))
            
            # Bỏ ảnh quá nhỏ
            if img.width < 50 or img.height < 50:
                print(f"Ảnh quá nhỏ ({img.width}x{img.height}): {url}")
                return False
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.save(save_path, 'JPEG', quality=95)
            print(f"Đã lưu: {save_path.name}")
            return True
            
        except Exception as e:
            print(f"Lỗi download {url}: {e}")
            return False
    
    def scrape_google_images_selenium(self, query, category, max_images=300, scroll_times=10):
        # Scrape Google Images dùng Selenium
        print(f"\nTìm kiếm Google Images (Selenium): '{query}' (category: {category})")
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)
        
        try:
            driver.get("https://www.google.com/imghp")
            wait = WebDriverWait(driver, 10)
            
            search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
            search_box.send_keys(query)
            search_box.send_keys(Keys.ENTER)
            
            # Cuộn để tải thêm ảnh
            for _ in range(scroll_times):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            img_elements = driver.find_elements(By.CSS_SELECTOR, "img.rg_i")
            
            count = 0
            for img in img_elements[:max_images]:
                if count >= max_images:
                    break
                
                try:
                    img.click()
                    time.sleep(1)
                    large_img = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.sFlh5c.pT0Scc.iPVvYb")))
                    img_url = large_img.get_attribute("src")
                except:
                    img_url = img.get_attribute("src") or img.get_attribute("data-src")
                
                if not img_url or img_url.startswith('data:'):
                    continue
                
                filename = f"{category}_{int(time.time())}_{count}.jpg"
                save_path = self.output_dir / category / filename
                
                if self.download_image(img_url, save_path):
                    self.metadata.append({
                        'filename': filename,
                        'category': category,
                        'source': 'google_images_selenium',
                        'query': query,
                        'url': img_url
                    })
                    count += 1
                
                time.sleep(1)
            
            print(f"Đã scrape {count} ảnh cho '{query}'")
            return count
            
        except Exception as e:
            print(f"Lỗi scrape Google Images Selenium: {e}")
            return 0
        finally:
            driver.quit()
    
    def scrape_bing_images(self, query, category, max_images=300):
        # Scrape Bing Images dùng requests + BS4
        print(f"\nTìm kiếm Bing Images: '{query}' (category: {category})")
        
        base_url = f"https://www.bing.com/images/search?q={query}"
        count = 0
        
        for page in range(1, 11):
            url = f"{base_url}&first={(page-1)*35}"
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            img_tags = soup.find_all('img', {'class': 'mimg'})
            
            for i, img in enumerate(img_tags):
                img_url = img.get('src') or img.get('data-src')
                if not img_url or img_url.startswith('data:'):
                    continue
                
                filename = f"{category}_{int(time.time())}_{count}.jpg"
                save_path = self.output_dir / category / filename
                
                if self.download_image(img_url, save_path):
                    self.metadata.append({
                        'filename': filename,
                        'category': category,
                        'source': 'bing_images',
                        'query': query,
                        'url': img_url
                    })
                    count += 1
                    if count >= max_images:
                        break
                
                time.sleep(0.5)
            
            if count >= max_images:
                break
        
        print(f"Đã scrape {count} ảnh cho '{query}'")
        return count

def main():
    print("Traffic Sign Web Scraper Nâng cấp")
    print("="*60)
    
    scraper = TrafficSignScraper()
    
    # Danh sách từ khóa tìm kiếm
    keywords = {
        'prohibitory': [
            'biển báo cấm giao thông việt nam',
            'biển cấm đỗ xe',
            'biển cấm rẽ trái',
            'biển giới hạn tốc độ việt nam',
            'biển cấm xe máy'
        ],
        'warning': [
            'biển báo cảnh báo giao thông việt nam',
            'biển cảnh báo đường trơn',
            'biển cảnh báo sạt lở',
            'biển cảnh báo trẻ em',
            'biển cảnh báo động vật'
        ],
        'mandatory': [
            'biển báo hiệu lệnh giao thông việt nam',
            'biển bắt buộc rẽ phải',
            'biển bắt buộc đi thẳng',
            'biển hiệu lệnh dành cho xe đạp',
            'biển bắt buộc giảm tốc'
        ],
        'informative': [
            'biển báo chỉ dẫn giao thông việt nam',
            'biển chỉ dẫn bệnh viện',
            'biển chỉ dẫn trạm xăng',
            'biển chỉ dẫn đường cao tốc',
            'biển chỉ dẫn khu dân cư'
        ]
    }
    
    total_scraped = 0
    for category, kw_list in keywords.items():
        for kw in kw_list:
            scraped = scraper.scrape_google_images_selenium(kw, category, max_images=200)
            if scraped < 50:
                scraped += scraper.scrape_bing_images(kw, category, max_images=200 - scraped)
            total_scraped += scraped
    
    scraper.save_metadata()
    
    stats = scraper.get_statistics()
    print("\nTHỐNG KÊ SAU SCRAPE:")
    for cat, count in stats.items():
        print(f"  - {cat}: {count} ảnh")
    print(f"  Tổng: {sum(stats.values())} ảnh")

if __name__ == '__main__':
    main()