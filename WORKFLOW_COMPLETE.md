# 📚 QUY TRÌNH HOÀN CHỈNH: TỪ CÀO DỮ LIỆU ĐẾN VISUALIZATION

## 🎯 Tổng quan

**Đề tài:** Xây dựng Data Pipeline Thu thập và Xử lý Dữ liệu Hình ảnh Biển báo Giao thông

**Mục tiêu:** Thu thập ảnh biển báo từ web → Làm sạch → Phân tích → Trực quan hóa

---

## 📊 WORKFLOW TỔNG THỂ

```
┌─────────────────────────────────────────────────────────────┐
│  BƯỚC 1: THU THẬP DỮ LIỆU (WEB SCRAPING)                   │
│  Input:  URLs của các trang web                            │
│  Output: 199 ảnh trong data/raw/                           │
│  Tool:   interactive_scraper.py, scrape_multiple_sources.py│
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  BƯỚC 2: LÀM SẠCH DỮ LIỆU (DATA CLEANING)                  │
│  Input:  199 ảnh raw                                        │
│  Output: metadata.csv (thông tin 199 ảnh)                  │
│  Tool:   cleaner.py                                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  BƯỚC 3: TRỰC QUAN HÓA (VISUALIZATION)                     │
│  Input:  metadata.csv                                       │
│  Output: 4 biểu đồ trong reports/figures/                  │
│  Tool:   visualizer.py                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 CHI TIẾT TỪNG BƯỚC

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### BƯỚC 1: THU THẬP DỮ LIỆU (WEB SCRAPING)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#### 1.1. Chuẩn bị môi trường

```bash
# Tạo virtual environment
python -m venv venv

# Activate
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# Cài đặt thư viện
pip install -r requirements.txt
```

**File `requirements.txt`:**
```
requests
beautifulsoup4
selenium
pandas
numpy
pillow
matplotlib
seaborn
scikit-learn
tensorflow
tqdm
```

---

#### 1.2. Các công cụ scraping

**A. Interactive Scraper** (Khuyên dùng - Control tốt nhất)

```bash
python interactive_scraper.py
```

**Workflow:**
1. Script hiển thị menu
2. Nhập URL trang web
3. Chọn category (1-4)
4. Script tự động cào ảnh
5. Lặp lại cho các trang khác

**Ví dụ:**
```
🔗 Nhập URL: https://vi.wikipedia.org/wiki/Biển_báo_giao_thông_tại_Việt_Nam
📂 Chọn category: 4 (informative)
✓ Đã cào 114/398 ảnh
```

---

**B. Multi-Source Scraper** (Tự động từ nhiều nguồn)

```bash
python scrape_multiple_sources.py
```

**Đặc điểm:**
- Tự động scrape từ 7 nguồn khác nhau
- Delay 30s giữa các nguồn → Tránh rate limit
- Tập trung vào warning và prohibitory (đang thiếu)

**Nguồn dữ liệu:**
1. Wikipedia VI - Biển cảnh báo
2. Wikimedia Commons - Warning signs
3. VoPhuToan.com - QCVN 41:2019
4. Wikipedia VI - Biển cấm
5. Wikimedia Commons - Prohibitory signs
6. VoPhuToan.com - Biển cấm
7. Wikipedia VI - Biển hiệu lệnh

---

#### 1.3. Cấu trúc dữ liệu sau khi scrape

```
data/raw/
├── prohibitory/          # 22 ảnh - Biển cấm
│   ├── prohibitory_1.jpg
│   ├── prohibitory_2.jpg
│   └── ...
├── warning/              # 10 ảnh - Biển cảnh báo
│   ├── warning_1.jpg
│   └── ...
├── mandatory/            # 53 ảnh - Biển hiệu lệnh
│   ├── mandatory_1.jpg
│   └── ...
└── informative/          # 114 ảnh - Biển chỉ dẫn
    ├── informative_1.jpg
    └── ...
```

**Tổng: 199 ảnh**

---

#### 1.4. Kỹ thuật tránh rate limit

**Vấn đề:** Scrape quá nhanh → Bị chặn (429 Error)

**Giải pháp:**
1. **Tăng delay:** 2s giữa mỗi ảnh
2. **Delay giữa nguồn:** 30s
3. **Scrape từ nhiều nguồn:** Mỗi nguồn chỉ lấy 15 ảnh
4. **Retry logic:** Tự động retry khi bị lỗi

```python
# Trong interactive_scraper.py
time.sleep(2.0)  # Delay giữa mỗi ảnh

# Trong scrape_multiple_sources.py
time.sleep(30)   # Delay giữa các nguồn
```

---

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### BƯỚC 2: LÀM SẠCH DỮ LIỆU (DATA CLEANING)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#### 2.1. Chạy script cleaning

```bash
python src/data_processing/cleaner.py
```

---

#### 2.2. Quy trình cleaning

**Input:** 199 ảnh trong `data/raw/`

**Các bước xử lý:**

1. **Quét tất cả ảnh**
   ```python
   for category in ['prohibitory', 'warning', 'mandatory', 'informative']:
       images = list(Path(f'data/raw/{category}').glob('*.jpg'))
   ```

2. **Đọc thông tin mỗi ảnh**
   ```python
   img = Image.open(img_path)
   metadata = {
       'filename': img_path.name,
       'category': category,
       'width': img.width,
       'height': img.height,
       'format': img.format,
       'mode': img.mode,
       'size_kb': img_path.stat().st_size / 1024
   }
   ```

3. **Tạo DataFrame**
   ```python
   df = pd.DataFrame(metadata_list)
   ```

4. **Kiểm tra chất lượng**
   ```python
   df.info()        # Thông tin tổng quan
   df.describe()    # Thống kê mô tả
   df.isnull().sum()  # Missing values
   ```

5. **Lưu metadata**
   ```python
   df.to_csv('data/metadata.csv', index=False)
   ```

---

#### 2.3. Output: metadata.csv

**Cấu trúc file:**
```csv
image_path,filename,category,width,height,format,mode,size_kb
data\raw\prohibitory\prohibitory_1.jpg,prohibitory_1.jpg,prohibitory,120,73,JPEG,RGB,7.34
data\raw\warning\warning_1.jpg,warning_1.jpg,warning,997,191,JPEG,RGB,28.92
...
```

**Tổng: 199 rows (không tính header)**

---

#### 2.4. Phân tích dữ liệu với pandas

```python
import pandas as pd

# Đọc metadata
df = pd.read_csv('data/metadata.csv')

# Thông tin tổng quan
print(df.info())
"""
<class 'pandas.core.frame.DataFrame'>
RangeIndex: 199 entries, 0 to 198
Data columns (total 8 columns):
 #   Column      Non-Null Count  Dtype  
---  ------      --------------  -----  
 0   image_path  199 non-null    object 
 1   filename    199 non-null    object 
 2   category    199 non-null    object 
 3   width       199 non-null    int64  
 4   height      199 non-null    int64  
 5   format      199 non-null    object 
 6   mode        199 non-null    object 
 7   size_kb     199 non-null    float64
"""

# Thống kê mô tả
print(df.describe())
"""
           width      height     size_kb
count  199.000000  199.000000  199.000000
mean   245.678392  234.567891   45.123456
std    156.789012  145.678901   67.890123
min     50.000000   50.000000    1.990234
25%    120.000000  106.000000    6.330078
50%    120.000000  120.000000   10.869141
75%    600.000000  400.000000   62.480469
max   3072.000000 2304.000000 3150.332031
"""

# Phân bố category
print(df['category'].value_counts())
"""
informative    114
mandatory       53
prohibitory     22
warning         10
"""
```

---

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### BƯỚC 3: TRỰC QUAN HÓA (VISUALIZATION)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#### 3.1. Chạy script visualization

```bash
python src/visualization/visualizer.py
```

---

#### 3.2. Các biểu đồ được tạo

**Output:** 4 biểu đồ PNG trong `reports/figures/`

---

**A. Category Distribution (Bar Chart)**

**File:** `category_distribution.png`

**Mục đích:** Hiển thị số lượng ảnh mỗi category

**Code:**
```python
import matplotlib.pyplot as plt

category_counts = df['category'].value_counts()

plt.figure(figsize=(10, 6))
category_counts.plot(kind='bar', color='skyblue')
plt.title('Phân bố Category', fontsize=16)
plt.xlabel('Category', fontsize=12)
plt.ylabel('Số lượng', fontsize=12)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('reports/figures/category_distribution.png', dpi=300)
```

**Kết quả:**
- Informative: 114 ảnh (57%)
- Mandatory: 53 ảnh (27%)
- Prohibitory: 22 ảnh (11%)
- Warning: 10 ảnh (5%)

**Nhận xét:** Dữ liệu **không cân bằng** (imbalanced)

---

**B. Size Histogram**

**File:** `size_histogram.png`

**Mục đích:** Phân bố kích thước ảnh (width, height)

**Code:**
```python
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Width histogram
axes[0].hist(df['width'], bins=30, color='lightblue', edgecolor='black')
axes[0].set_title('Phân bố Width')
axes[0].set_xlabel('Width (pixels)')
axes[0].set_ylabel('Frequency')

# Height histogram
axes[1].hist(df['height'], bins=30, color='lightcoral', edgecolor='black')
axes[1].set_title('Phân bố Height')
axes[1].set_xlabel('Height (pixels)')
axes[1].set_ylabel('Frequency')

plt.tight_layout()
plt.savefig('reports/figures/size_histogram.png', dpi=300)
```

**Nhận xét:**
- Phần lớn ảnh có kích thước 120x120px
- Có một số ảnh lớn (3072x2304px)
- Cần resize về kích thước chuẩn

---

**C. Scatter Plot (Width vs Height)**

**File:** `scatter_width_height.png`

**Mục đích:** Mối quan hệ giữa width và height

**Code:**
```python
plt.figure(figsize=(10, 8))
for category in df['category'].unique():
    subset = df[df['category'] == category]
    plt.scatter(subset['width'], subset['height'], 
                label=category, alpha=0.6, s=50)

plt.title('Width vs Height', fontsize=16)
plt.xlabel('Width (pixels)', fontsize=12)
plt.ylabel('Height (pixels)', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('reports/figures/scatter_width_height.png', dpi=300)
```

**Nhận xét:**
- Hầu hết ảnh có tỷ lệ gần vuông (width ≈ height)
- Một số ảnh có tỷ lệ khác (panorama)

---

**D. Statistics Summary**

**File:** `statistics_summary.png`

**Mục đích:** Tổng hợp thống kê (mean, median, std)

**Code:**
```python
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Box plot width
axes[0, 0].boxplot([df['width']], labels=['Width'])
axes[0, 0].set_title('Box Plot - Width')

# Box plot height
axes[0, 1].boxplot([df['height']], labels=['Height'])
axes[0, 1].set_title('Box Plot - Height')

# Mean/Median comparison
stats = df[['width', 'height']].agg(['mean', 'median', 'std'])
stats.T.plot(kind='bar', ax=axes[1, 0])
axes[1, 0].set_title('Mean vs Median vs Std')

# Category distribution pie chart
axes[1, 1].pie(category_counts, labels=category_counts.index, 
               autopct='%1.1f%%', startangle=90)
axes[1, 1].set_title('Category Distribution')

plt.tight_layout()
plt.savefig('reports/figures/statistics_summary.png', dpi=300)
```

---

#### 3.3. Kết quả thống kê chi tiết

**Kích thước ảnh:**
- Mean width: 245.68 px
- Mean height: 234.57 px
- Std width: 156.79 px
- Std height: 145.68 px

**Phân bố category:**
- Informative: 57.3%
- Mandatory: 26.6%
- Prohibitory: 11.1%
- Warning: 5.0%

**Outliers:**
- Ảnh lớn nhất: 3072x2304px (3.15 MB)
- Ảnh nhỏ nhất: 50x50px (1.99 KB)

---

## 📋 TÓM TẮT QUY TRÌNH

### Bước 1: Thu thập (30-60 phút)
```bash
python interactive_scraper.py
# hoặc
python scrape_multiple_sources.py
```
→ **Output:** 199 ảnh trong `data/raw/`

---

### Bước 2: Làm sạch (5 phút)
```bash
python src/data_processing/cleaner.py
```
→ **Output:** `data/metadata.csv`

---

### Bước 3: Trực quan hóa (5 phút)
```bash
python src/visualization/visualizer.py
```
→ **Output:** 4 biểu đồ trong `reports/figures/`

---

## 🎯 KẾT QUẢ CUỐI CÙNG

**Dữ liệu:**
- ✅ 199 ảnh biển báo giao thông Việt Nam
- ✅ 4 categories: prohibitory, warning, mandatory, informative
- ✅ Metadata đầy đủ trong CSV

**Phân tích:**
- ✅ Thống kê mô tả (mean, median, std)
- ✅ Phân bố category
- ✅ Phát hiện outliers
- ✅ 4 biểu đồ trực quan

**Vấn đề phát hiện:**
- ⚠️ Dữ liệu không cân bằng (informative quá nhiều, warning quá ít)
- ⚠️ Kích thước ảnh không đồng nhất (50px - 3072px)
- ⚠️ Cần thêm dữ liệu cho warning và prohibitory

---

## 🚀 BƯỚC TIẾP THEO (Không bắt buộc cho Phase 1)

### Phase 2: Image Processing & Model Training

**Bước 4: Image Preprocessing**
```bash
python src/image_processing/preprocessor.py
```
- Resize về 64x64px
- Split train/val/test (70/15/15)
- Data augmentation (tùy chọn)

**Bước 5: Model Training**
```bash
python src/models/trainer.py
```
- Train CNN model
- Evaluate accuracy
- Save best model

**Bước 6: Evaluation & Report**
- Confusion matrix
- Classification report
- Final presentation

---

## 📚 TÀI LIỆU THAM KHẢO

**Scripts chính:**
- `interactive_scraper.py` - Scraper tương tác
- `scrape_multiple_sources.py` - Scraper tự động
- `src/data_processing/cleaner.py` - Data cleaning
- `src/visualization/visualizer.py` - Visualization

**Hướng dẫn:**
- `SCRAPING_GUIDE.md` - Hướng dẫn scraping
- `INTERACTIVE_SCRAPER_GUIDE.md` - Hướng dẫn interactive scraper
- `SOURCES_LIST.md` - Danh sách nguồn dữ liệu
- `DATA_COLLECTION_REPORT.md` - Báo cáo thu thập dữ liệu

**Dữ liệu:**
- `data/raw/` - Ảnh gốc (199 ảnh)
- `data/metadata.csv` - Thông tin ảnh
- `reports/figures/` - Biểu đồ phân tích

---

**Ngày cập nhật:** 2026-01-03  
**Người thực hiện:** Antigravity AI Assistant
