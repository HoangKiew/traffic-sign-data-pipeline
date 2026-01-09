# 📚 TRẢ LỜI THẦY: CÔNG NGHỆ & PHƯƠNG PHÁP THU THẬP DỮ LIỆU

## ❓ CÂU HỎI CỦA THẦY

**"Em lấy dữ liệu bằng cách nào? Dùng công nghệ gì? Công cụ gì?"**

---

## ✅ CÂU TRẢ LỜI CHUẨN

### 1. PHƯƠNG PHÁP THU THẬP DỮ LIỆU

**Em sử dụng phương pháp:** **Web Scraping** (Cào dữ liệu từ web)

**Lý do chọn:**
- ✅ Thu thập dữ liệu **thô** (raw data) từ nguồn gốc
- ✅ Không sử dụng dataset có sẵn (theo yêu cầu đề tài)
- ✅ Dữ liệu **đa dạng** từ nhiều nguồn khác nhau
- ✅ Học được kỹ năng **data collection** thực tế

---

### 2. CÔNG NGHỆ & CÔNG CỤ SỬ DỤNG

#### A. **Ngôn ngữ lập trình:** Python 3.x

**Lý do:**
- Thư viện phong phú cho web scraping
- Dễ xử lý dữ liệu với pandas
- Phổ biến trong Data Science

---

#### B. **Thư viện Web Scraping:**

**1. Requests** (HTTP Client)
```python
import requests
response = requests.get(url)
```
- **Chức năng:** Gửi HTTP request, tải nội dung trang web
- **Vai trò:** Lấy HTML của trang web (giống mở trình duyệt)

**2. BeautifulSoup4** (HTML Parser)
```python
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')
images = soup.find_all('img')
```
- **Chức năng:** Parse HTML, tìm kiếm elements
- **Vai trò:** Trích xuất thông tin từ HTML (tìm thẻ `<img>`)

**3. Pillow (PIL)** (Image Processing)
```python
from PIL import Image
img = Image.open('image.jpg')
```
- **Chức năng:** Đọc, validate, xử lý ảnh
- **Vai trò:** Kiểm tra kích thước, format, chất lượng ảnh

---

#### C. **Thư viện Data Processing:**

**4. Pandas** (Data Analysis)
```python
import pandas as pd
df = pd.DataFrame(metadata)
```
- **Chức năng:** Xử lý dữ liệu dạng bảng
- **Vai trò:** Tạo metadata, phân tích thống kê

**5. NumPy** (Numerical Computing)
```python
import numpy as np
```
- **Chức năng:** Tính toán số học
- **Vai trò:** Xử lý outliers, thống kê

---

#### D. **Thư viện Visualization:**

**6. Matplotlib** (Plotting)
```python
import matplotlib.pyplot as plt
plt.bar(categories, counts)
```
- **Chức năng:** Vẽ biểu đồ
- **Vai trò:** Tạo bar chart, histogram, scatter plot

**7. Seaborn** (Statistical Visualization)
```python
import seaborn as sns
sns.heatmap(data)
```
- **Chức năng:** Biểu đồ thống kê đẹp hơn
- **Vai trò:** Tạo visualization chuyên nghiệp

---

#### E. **Thư viện Hash Detection:**

**8. hashlib** (Built-in)
```python
import hashlib
md5 = hashlib.md5(data).hexdigest()
```
- **Chức năng:** Tính MD5 hash
- **Vai trò:** Phát hiện ảnh trùng lặp (exact duplicates)

**9. imagehash** (Perceptual Hashing)
```python
import imagehash
phash = imagehash.average_hash(img)
```
- **Chức năng:** Tính perceptual hash
- **Vai trò:** Phát hiện ảnh tương tự (similar images)

---

### 3. NGUỒN DỮ LIỆU

**Em thu thập từ các nguồn chính thức:**

1. **Wikipedia tiếng Việt**
   - URL: https://vi.wikipedia.org/wiki/Biển_báo_giao_thông_tại_Việt_Nam
   - Loại: Trang web tĩnh (static)
   - Kết quả: 114 ảnh

2. **Wikimedia Commons**
   - URL: https://commons.wikimedia.org/wiki/Category:Road_signs_in_Vietnam
   - Loại: Trang web tĩnh
   - Kết quả: 13 ảnh

3. **VoPhuToan.com** (QCVN 41:2019)
   - URL: https://vophutoan.com/tai-lieu/tieu-chuan/qcvn-412019-bgtvt-bao-hieu-duong-bo/
   - Loại: Trang web tĩnh
   - Kết quả: 20 ảnh

4. **ThuVienPhapLuat.vn**
   - URL: https://thuvienphapluat.vn/...
   - Loại: Trang web tĩnh
   - Kết quả: 52 ảnh

**Tổng:** 199 ảnh từ 4 nguồn

---

### 4. QUY TRÌNH THU THẬP (WORKFLOW)

```
Bước 1: Gửi HTTP Request
   ↓ (Requests)
Bước 2: Nhận HTML response
   ↓
Bước 3: Parse HTML
   ↓ (BeautifulSoup)
Bước 4: Tìm tất cả thẻ <img>
   ↓
Bước 5: Lấy URL của ảnh
   ↓
Bước 6: Validate URL
   ↓
Bước 7: Download ảnh
   ↓ (Requests)
Bước 8: Validate ảnh
   ↓ (Pillow)
Bước 9: Lưu vào data/raw/
   ↓
Bước 10: Tạo metadata
   ↓ (Pandas)
Bước 11: Phát hiện duplicates
   ↓ (hashlib, imagehash)
Bước 12: Visualization
   ↓ (Matplotlib, Seaborn)
Hoàn tất!
```

---

### 5. KỸ THUẬT TRÁNH RATE LIMIT

**Vấn đề:** Scrape quá nhanh → Bị chặn (429 Error)

**Giải pháp:**
1. **Delay giữa requests:** 2 giây
2. **Delay giữa nguồn:** 30 giây
3. **Retry logic:** Tự động thử lại khi lỗi
4. **User-Agent rotation:** Giả lập nhiều trình duyệt
5. **Scrape từ nhiều nguồn:** Mỗi nguồn chỉ lấy ít ảnh

```python
import time
time.sleep(2)  # Delay 2s giữa mỗi request
```

---

### 6. VALIDATION & QUALITY CONTROL

**Kiểm tra chất lượng ảnh:**
- ✅ Kích thước tối thiểu: 50x50 pixels
- ✅ Format: JPEG, PNG
- ✅ Mode: RGB (convert nếu cần)
- ✅ Loại bỏ: Icons, SVG, ảnh quá nhỏ

```python
if img.width < 50 or img.height < 50:
    skip  # Bỏ qua ảnh quá nhỏ
```

---

### 7. KẾT QUẢ THU THẬP

**Dữ liệu thu được:**
- Tổng: **199 ảnh**
- Phân loại: 4 categories (prohibitory, warning, mandatory, informative)
- Format: JPEG
- Kích thước: 50px - 3072px
- Metadata: CSV file với 8 columns

**Chất lượng:**
- ✅ Không có duplicates (MD5 hash)
- ✅ Phát hiện 2 nhóm similar images (perceptual hash)
- ✅ Đa dạng nguồn (4 websites)

---

## 📊 BẢNG TỔNG HỢP CÔNG NGHỆ

| Công nghệ | Mục đích | Vai trò |
|-----------|----------|---------|
| **Python 3.x** | Ngôn ngữ chính | Lập trình |
| **Requests** | HTTP Client | Tải trang web |
| **BeautifulSoup4** | HTML Parser | Trích xuất ảnh |
| **Pillow** | Image Processing | Validate ảnh |
| **Pandas** | Data Analysis | Xử lý metadata |
| **NumPy** | Numerical Computing | Tính toán |
| **Matplotlib** | Plotting | Vẽ biểu đồ |
| **Seaborn** | Statistical Viz | Visualization |
| **hashlib** | Hashing | Detect duplicates |
| **imagehash** | Perceptual Hash | Detect similar |

---

## 💡 ƯU ĐIỂM PHƯƠNG PHÁP

1. ✅ **Tự động hóa:** Scrape hàng trăm ảnh tự động
2. ✅ **Đa dạng:** Nhiều nguồn khác nhau
3. ✅ **Chất lượng:** Validate kỹ lưỡng
4. ✅ **Reproducible:** Có thể chạy lại
5. ✅ **Scalable:** Dễ mở rộng thêm nguồn

---

## 📝 TÀI LIỆU THAM KHẢO

1. **Requests Documentation:** https://requests.readthedocs.io/
2. **BeautifulSoup Documentation:** https://www.crummy.com/software/BeautifulSoup/
3. **Pandas Documentation:** https://pandas.pydata.org/
4. **Matplotlib Documentation:** https://matplotlib.org/

---

**Tóm tắt cho thầy:**
> "Em sử dụng **Python** với các thư viện **Requests** và **BeautifulSoup** để scrape dữ liệu từ 4 nguồn web chính thức (Wikipedia, Wikimedia Commons, VoPhuToan, ThuVienPhapLuat). Sau đó dùng **Pandas** để xử lý metadata, **hashlib/imagehash** để phát hiện duplicates, và **Matplotlib/Seaborn** để visualization. Tổng cộng thu thập được **199 ảnh** biển báo giao thông Việt Nam."

---

**Ngày:** 2026-01-06  
**Sinh viên:** [Tên bạn]  
**Đề tài:** Xây dựng Data Pipeline Thu thập và Xử lý Dữ liệu Hình ảnh Biển báo Giao thông
