"""
Scraper chuyên biệt cho các nguồn biển báo giao thông Việt Nam
Scrape từ Wikipedia, Wikimedia Commons, và các trang web Việt Nam
"""

import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
from urllib.parse import urljoin, unquote
from PIL import Image
from io import BytesIO
import json
import re


class VietnameseTrafficSignScraper:
    """Scraper cho các nguồn biển báo Việt Nam"""
    
    def __init__(self, output_dir='data/raw'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Categories
        self.categories = {
            'prohibitory': ['cấm', 'prohibit', 'P.1', 'P.2', 'P.'],
            'warning': ['cảnh báo', 'warning', 'W.', 'nguy hiểm'],
            'mandatory': ['hiệu lệnh', 'mandatory', 'R.', 'bắt buộc'],
            'informative': ['chỉ dẫn', 'information', 'I.', 'hướng dẫn']
        }
        
        for cat in self.categories.keys():
            (self.output_dir / cat).mkdir(exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        self.metadata = []
        self.downloaded_urls = set()
    
    def categorize_sign(self, text):
        """Tự động phân loại biển báo dựa trên text"""
        text_lower = text.lower()
        
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return category
        
        return 'informative'  # Default
    
    def download_image(self, url, category, prefix='', timeout=15, max_retries=3):
        """Download và lưu ảnh với retry logic"""
        if url in self.downloaded_urls:
            return False
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=timeout)
                response.raise_for_status()
                
                # Validate image
                img = Image.open(BytesIO(response.content))
                
                # Filter small images
                if img.width < 80 or img.height < 80:
                    return False
                
                # Convert to RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Generate filename
                timestamp = int(time.time() * 1000)
                filename = f"{category}_{prefix}_{timestamp}.jpg"
                save_path = self.output_dir / category / filename
                
                # Save
                img.save(save_path, 'JPEG', quality=95)
                
                self.metadata.append({
                    'filename': filename,
                    'category': category,
                    'url': url,
                    'width': img.width,
                    'height': img.height
                })
                
                self.downloaded_urls.add(url)
                print(f"  ✓ {filename} ({img.width}x{img.height})")
                return True
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    wait_time = (attempt + 1) * 5  # Exponential backoff
                    print(f"  ⏳ Rate limited, đợi {wait_time}s...")
                    time.sleep(wait_time)
                    continue  # Retry
                else:
                    print(f"  ⚠️  HTTP Error: {e}")
                    return False
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"  ⚠️  Lỗi: {str(e)[:50]}")
                return False
        
        return False
    
    def scrape_wikipedia_vi(self):
        """
        Scrape Wikipedia tiếng Việt
        https://vi.wikipedia.org/wiki/Biển_báo_giao_thông_tại_Việt_Nam
        """
        url = 'https://vi.wikipedia.org/wiki/Bi%E1%BB%83n_b%C3%A1o_giao_th%C3%B4ng_t%E1%BA%A1i_Vi%E1%BB%87t_Nam'
        
        print("\n" + "="*70)
        print("🇻🇳 SCRAPING: Wikipedia Tiếng Việt")
        print("="*70)
        print(f"URL: {url}\n")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            count = 0
            
            # Tìm tất cả ảnh trong content
            content = soup.find('div', {'id': 'mw-content-text'})
            if not content:
                print("❌ Không tìm thấy content")
                return 0
            
            # Tìm tất cả thẻ img
            images = content.find_all('img')
            
            for img in images:
                src = img.get('src')
                if not src:
                    continue
                
                # Convert to absolute URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://vi.wikipedia.org' + src
                
                # Skip icons và logos
                if any(x in src.lower() for x in ['icon', 'logo', 'edit', 'magnify']):
                    continue
                
                # Get high resolution version
                src = src.replace('/thumb/', '/').rsplit('/', 1)[0] if '/thumb/' in src else src
                
                # Tìm context để categorize
                parent_text = img.find_parent(['p', 'div', 'td', 'li'])
                context = parent_text.get_text() if parent_text else ''
                
                # Auto categorize
                category = self.categorize_sign(context)
                
                if self.download_image(src, category, 'wiki_vi'):
                    count += 1
                
                time.sleep(0.5)
            
            print(f"\n✅ Wikipedia VI: Đã scrape {count} ảnh")
            return count
            
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return 0
    
    def scrape_wikimedia_commons(self):
        """
        Scrape Wikimedia Commons
        https://commons.wikimedia.org/w/index.php?search=Vietnam+Traffic+Sign
        """
        base_url = 'https://commons.wikimedia.org/w/index.php'
        search_queries = [
            'Vietnam Traffic Sign',
            'Vietnamese Road Sign',
            'Biển báo giao thông Việt Nam'
        ]
        
        print("\n" + "="*70)
        print("📷 SCRAPING: Wikimedia Commons")
        print("="*70)
        
        total_count = 0
        
        for query in search_queries:
            print(f"\n🔍 Query: {query}")
            
            params = {
                'search': query,
                'title': 'Special:MediaSearch',
                'type': 'image'
            }
            
            try:
                response = requests.get(base_url, params=params, headers=self.headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Tìm ảnh trong kết quả search
                img_links = soup.find_all('a', {'class': re.compile('sdms-image-result')})
                
                if not img_links:
                    # Fallback: tìm tất cả img
                    img_links = soup.find_all('img')
                
                count = 0
                for link in img_links[:30]:  # Limit 30 per query
                    # Tìm src
                    img = link.find('img') if link.name == 'a' else link
                    if not img:
                        continue
                    
                    src = img.get('src') or img.get('data-src')
                    if not src:
                        continue
                    
                    # Convert to full URL
                    if src.startswith('//'):
                        src = 'https:' + src
                    
                    # Skip thumbnails, get original
                    if 'thumb' in src:
                        # Try to get original
                        src = re.sub(r'/thumb/(.+)/\d+px-.+', r'/\1', src)
                    
                    # Auto categorize
                    alt_text = img.get('alt', '')
                    title = img.get('title', '')
                    context = f"{alt_text} {title}"
                    category = self.categorize_sign(context)
                    
                    if self.download_image(src, category, 'commons'):
                        count += 1
                    
                    time.sleep(0.5)
                
                print(f"  ✓ Query '{query}': {count} ảnh")
                total_count += count
                time.sleep(2)
                
            except Exception as e:
                print(f"  ❌ Lỗi query '{query}': {e}")
        
        print(f"\n✅ Wikimedia Commons: Tổng {total_count} ảnh")
        return total_count
    
    def scrape_vophutoan(self):
        """
        Scrape vophutoan.com
        https://vophutoan.com/tai-lieu/tieu-chuan/qcvn-412019-bgtvt-bao-hieu-duong-bo/
        """
        url = 'https://vophutoan.com/tai-lieu/tieu-chuan/qcvn-412019-bgtvt-bao-hieu-duong-bo/'
        
        print("\n" + "="*70)
        print("📋 SCRAPING: VoPhuToan.com (QCVN 41:2019)")
        print("="*70)
        print(f"URL: {url}\n")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            count = 0
            
            # Tìm content area
            content = soup.find('div', {'class': re.compile('entry-content|post-content|content')})
            if not content:
                content = soup.find('article') or soup
            
            # Tìm tất cả ảnh
            images = content.find_all('img')
            
            for img in images:
                src = img.get('src') or img.get('data-src')
                if not src:
                    continue
                
                # Convert to absolute URL
                src = urljoin(url, src)
                
                # Skip small images
                if any(x in src.lower() for x in ['icon', 'logo', 'avatar', 'banner']):
                    continue
                
                # Get context
                parent = img.find_parent(['figure', 'div', 'p'])
                context = ''
                if parent:
                    caption = parent.find(['figcaption', 'caption'])
                    context = caption.get_text() if caption else parent.get_text()
                
                # Auto categorize
                category = self.categorize_sign(context)
                
                if self.download_image(src, category, 'vophutoan'):
                    count += 1
                
                time.sleep(0.5)
            
            print(f"\n✅ VoPhuToan: Đã scrape {count} ảnh")
            return count
            
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return 0
    
    def scrape_thuvienphapluat(self):
        """
        Scrape thuvienphapluat.vn
        https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/ho-tro-phap-luat/tu-van-phap-luat/43161/tong-hop-cac-loai-bien-bao-hieu-lenh-va-y-nghia-cua-tung-bien-bao
        """
        url = 'https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/ho-tro-phap-luat/tu-van-phap-luat/43161/tong-hop-cac-loai-bien-bao-hieu-lenh-va-y-nghia-cua-tung-bien-bao'
        
        print("\n" + "="*70)
        print("⚖️  SCRAPING: ThuVienPhapLuat.vn")
        print("="*70)
        print(f"URL: {url}\n")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            count = 0
            
            # Tìm content
            content = soup.find('div', {'class': re.compile('content|article')})
            if not content:
                content = soup
            
            # Tìm tất cả ảnh
            images = content.find_all('img')
            
            for img in images:
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if not src:
                    continue
                
                # Convert to absolute URL
                src = urljoin(url, src)
                
                # Skip icons
                if any(x in src.lower() for x in ['icon', 'logo', 'banner']):
                    continue
                
                # Get context
                alt = img.get('alt', '')
                title = img.get('title', '')
                parent = img.find_parent(['p', 'div', 'td'])
                parent_text = parent.get_text() if parent else ''
                
                context = f"{alt} {title} {parent_text}"
                
                # Auto categorize
                category = self.categorize_sign(context)
                
                if self.download_image(src, category, 'thuvienpl'):
                    count += 1
                
                time.sleep(0.5)
            
            print(f"\n✅ ThuVienPhapLuat: Đã scrape {count} ảnh")
            return count
            
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return 0
    
    def scrape_all_sources(self):
        """Scrape tất cả các nguồn"""
        print("\n" + "="*70)
        print("🚀 BẮT ĐẦU SCRAPING TẤT CẢ NGUỒN")
        print("="*70)
        
        total = 0
        
        # 1. Wikipedia VI
        total += self.scrape_wikipedia_vi()
        time.sleep(3)
        
        # 2. Wikimedia Commons
        total += self.scrape_wikimedia_commons()
        time.sleep(3)
        
        # 3. VoPhuToan
        total += self.scrape_vophutoan()
        time.sleep(3)
        
        # 4. ThuVienPhapLuat
        total += self.scrape_thuvienphapluat()
        
        return total
    
    def save_metadata(self):
        """Lưu metadata"""
        metadata_file = self.output_dir / 'vietnamese_sources_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Đã lưu metadata: {metadata_file}")
    
    def get_statistics(self):
        """Thống kê"""
        stats = {}
        for category in self.categories.keys():
            count = len(list((self.output_dir / category).glob('*.jpg')))
            stats[category] = count
        return stats


def main():
    """Main function"""
    print("🇻🇳 VIETNAMESE TRAFFIC SIGN SCRAPER")
    print("="*70)
    
    scraper = VietnameseTrafficSignScraper()
    
    # Scrape all
    total = scraper.scrape_all_sources()
    
    # Save metadata
    scraper.save_metadata()
    
    # Statistics
    print("\n" + "="*70)
    print("📊 THỐNG KÊ KẾT QUẢ")
    print("="*70)
    
    stats = scraper.get_statistics()
    print(f"\n🎯 Tổng số ảnh đã scrape: {total}")
    print(f"📁 Phân bố theo category:")
    for category, count in stats.items():
        print(f"   - {category:15s}: {count:3d} ảnh")
    
    print("\n" + "="*70)
    print("✅ HOÀN TẤT!")
    print("="*70)
    print(f"📂 Dữ liệu: {scraper.output_dir}")
    print(f"📋 Metadata: {scraper.output_dir}/vietnamese_sources_metadata.json")


if __name__ == '__main__':
    main()
