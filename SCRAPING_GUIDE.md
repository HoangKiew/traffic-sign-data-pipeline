# Hướng dẫn Thu thập Dữ liệu THÔ (Web Scraping)

## 🎯 Mục tiêu
Thu thập dữ liệu hình ảnh biển báo giao thông **TỰ SCRAPE** từ web, KHÔNG dùng dataset có sẵn.

---

## 📋 Các phương pháp thu thập

### 1. **Scraper cơ bản** (`scraper.py`)
Dùng `requests` + `BeautifulSoup` cho các trang web tĩnh.

**Ưu điểm:**
- Nhanh, nhẹ
- Không cần browser

**Nhược điểm:**
- Không scrape được trang JavaScript
- Dễ bị block

**Cách dùng:**
```python
from src.data_collection.scraper import TrafficSignScraper

scraper = TrafficSignScraper()

# Cách 1: Scrape từ danh sách URLs
scraper.scrape_from_url_list('urls.txt', 'prohibitory')

# Cách 2: Scrape từ website
scraper.scrape_website('https://example.com', 'warning')

# Lưu metadata
scraper.save_metadata()
```

---

### 2. **Selenium Scraper** (`selenium_scraper.py`)
Dùng Selenium để scrape trang động (Google Images, v.v.)

**Ưu điểm:**
- Scrape được trang JavaScript
- Có thể scroll, click, tương tác

**Nhược điểm:**
- Chậm hơn
- Cần ChromeDriver

**Setup ChromeDriver:**
```bash
# Cách 1: Download manual
# https://chromedriver.chromium.org/

# Cách 2: Dùng webdriver-manager
pip install webdriver-manager
```

**Cách dùng:**
```python
from src.data_collection.selenium_scraper import SeleniumScraper

scraper = SeleniumScraper(headless=False)
scraper.start_driver()

# Scrape Google Images
scraper.scrape_google_images_advanced(
    query='biển cấm đường Việt Nam',
    category='prohibitory',
    max_images=100
)

scraper.save_metadata()
scraper.close_driver()
```

---

## 🌐 Nguồn dữ liệu đề xuất

### A. Trang web Việt Nam
1. **Cục CSGT - Bộ Công an**
   - Website: https://csgt.vn/
   - Có hình ảnh biển báo chính thức

2. **Bộ GTVT**
   - Tài liệu về biển báo giao thông

3. **Wikipedia tiếng Việt**
   - https://vi.wikipedia.org/wiki/Biển_báo_giao_thông_tại_Việt_Nam

### B. Google Images
```python
queries = [
    'biển cấm đường Việt Nam',
    'biển cảnh báo giao thông',
    'biển hiệu lệnh giao thông',
    'biển chỉ dẫn đường bộ',
    'traffic signs Vietnam',
    'Vietnamese road signs'
]
```

### C. Tự chụp ảnh
- Đi chụp ảnh biển báo thực tế trên đường
- Đảm bảo chất lượng ảnh tốt

---

## 📝 Workflow thu thập dữ liệu

### Bước 1: Chuẩn bị danh sách URLs
Tạo file `urls.txt` với URLs ảnh:
```
https://example.com/image1.jpg
https://example.com/image2.jpg
https://example.com/image3.jpg
```

### Bước 2: Chạy scraper
```bash
# Activate venv
.\venv\Scripts\Activate.ps1

# Chạy scraper
python src/data_collection/scraper.py
```

### Bước 3: Kiểm tra dữ liệu
```bash
# Xem số lượng ảnh đã scrape
ls data/raw/prohibitory/
ls data/raw/warning/
ls data/raw/mandatory/
ls data/raw/informative/
```

### Bước 4: Clean và xử lý
```bash
# Chạy data cleaning
python src/data_processing/cleaner.py
```

---

## 🎯 Mục tiêu thu thập

| Category | Mục tiêu | Mô tả |
|----------|----------|-------|
| **Prohibitory** (Biển cấm) | 200+ ảnh | Cấm đường, cấm rẽ, cấm dừng, v.v. |
| **Warning** (Biển cảnh báo) | 200+ ảnh | Nguy hiểm, chú ý, v.v. |
| **Mandatory** (Biển hiệu lệnh) | 150+ ảnh | Bắt buộc rẽ, chỉ đường, v.v. |
| **Informative** (Biển chỉ dẫn) | 150+ ảnh | Thông tin đường, địa điểm, v.v. |

**Tổng:** ~700-1000 ảnh

---

## ⚠️ Lưu ý quan trọng

### 1. Tuân thủ luật bản quyền
- Chỉ scrape cho mục đích học tập
- Không sử dụng thương mại
- Tôn trọng `robots.txt`

### 2. Tránh bị block
```python
# Thêm delay giữa các requests
time.sleep(1)

# Dùng headers giống browser thật
headers = {
    'User-Agent': 'Mozilla/5.0 ...'
}

# Rotate IP nếu cần (dùng proxy)
```

### 3. Validate chất lượng ảnh
- Kích thước tối thiểu: 100x100 pixels
- Format: JPG, PNG
- Loại bỏ ảnh bị lỗi, mờ

---

## 🚀 Script tự động hoá

Tạo file `auto_scrape.py`:
```python
from src.data_collection.selenium_scraper import SeleniumScraper
import time

scraper = SeleniumScraper(headless=True)
scraper.start_driver()

queries = [
    ('biển cấm đường Việt Nam', 'prohibitory', 50),
    ('biển cảnh báo giao thông Việt Nam', 'warning', 50),
    ('biển hiệu lệnh giao thông', 'mandatory', 40),
    ('biển chỉ dẫn đường', 'informative', 40),
]

for query, category, max_imgs in queries:
    print(f"\n{'='*60}")
    print(f"Scraping: {query}")
    print(f"{'='*60}")
    
    scraper.scrape_google_images_advanced(query, category, max_imgs)
    time.sleep(10)  # Delay giữa các queries

scraper.save_metadata()
scraper.close_driver()

print("\n✅ Hoàn tất scraping!")
```

Chạy:
```bash
python auto_scrape.py
```

---

## 📊 Kiểm tra kết quả

```python
from src.data_collection.scraper import TrafficSignScraper

scraper = TrafficSignScraper()
stats = scraper.get_statistics()

print("📊 Thống kê:")
for category, count in stats.items():
    print(f"  {category}: {count} ảnh")
```

---

## ✅ Checklist

- [ ] Cài đặt ChromeDriver (nếu dùng Selenium)
- [ ] Chuẩn bị danh sách URLs hoặc queries
- [ ] Chạy scraper thu thập ảnh
- [ ] Kiểm tra số lượng và chất lượng ảnh
- [ ] Chạy data cleaning
- [ ] Tạo visualizations
- [ ] Tiến hành preprocessing cho model

---

**Good luck! 🚦**
