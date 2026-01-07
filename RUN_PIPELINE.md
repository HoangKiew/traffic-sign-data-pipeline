# 🚀 HƯỚNG DẪN CHẠY PIPELINE TỪNG BƯỚC

## 📋 Tổng quan

Pipeline gồm **4 bước chính**, chạy tuần tự:

```
1. Scraping → 2. Cleaning → 3. Visualization → 4. Preprocessing
```

---

## ⚙️ CHUẨN BỊ

### Bước 0: Activate virtual environment

```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Hoặc CMD
.\venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

**Kiểm tra:** Dòng lệnh sẽ có `(venv)` ở đầu

---

## 📊 PIPELINE CHI TIẾT

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### BƯỚC 1: WEB SCRAPING (Thu thập dữ liệu)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Mục đích:** Thu thập ảnh biển báo từ web

**Lệnh:**
```bash
python src/data_collection/scraper.py
```

**Input:** URLs của các trang web (trong code)

**Output:**
- `data/raw/prohibitory/` - Ảnh biển cấm
- `data/raw/warning/` - Ảnh biển cảnh báo
- `data/raw/mandatory/` - Ảnh biển hiệu lệnh
- `data/raw/informative/` - Ảnh biển chỉ dẫn

**Thời gian:** ~30-60 phút (tùy số lượng ảnh)

**Kết quả mong đợi:**
```
✓ Đã scrape 199 ảnh
  - prohibitory: 22 ảnh
  - warning: 10 ảnh
  - mandatory: 53 ảnh
  - informative: 114 ảnh
```

**Kiểm tra:**
```bash
# Đếm số ảnh đã scrape
ls data\raw\*\*.jpg | Measure-Object | Select-Object -ExpandProperty Count
```

---

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### BƯỚC 2: DATA CLEANING (Làm sạch dữ liệu)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Mục đích:** Tạo metadata, phát hiện duplicates & similar images

**Lệnh:**
```bash
python src/data_processing/cleaner.py
```

**Input:** Ảnh trong `data/raw/`

**Output:**
- `data/metadata.csv` - File CSV chứa thông tin 199 ảnh

**Thời gian:** ~1-2 phút

**Kết quả mong đợi:**
```
🚀 Data Cleaning Pipeline
============================================================
📊 Đang tạo metadata từ raw images...
✓ Đã tạo metadata cho 199 images

🔐 Đang tính MD5 hash...
✓ Đã tính MD5 hash cho 199 images

🎨 Đang tính Perceptual hash...
✓ Đã tính Perceptual hash cho 199 images

🔍 Tìm exact duplicates (MD5)...
✓ Không có ảnh trùng lặp

🔎 Tìm similar images (threshold=5)...
⚠️  Tìm thấy 2 nhóm ảnh tương tự

📋 THÔNG TIN DỮ LIỆU (df.info())
...

✅ Hoàn tất Data Cleaning!
💾 Đã lưu: data/metadata.csv
```

**Kiểm tra:**
```bash
# Xem metadata
head data\metadata.csv
```

---

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### BƯỚC 3: VISUALIZATION (Trực quan hóa)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Mục đích:** Tạo biểu đồ phân tích dữ liệu

**Lệnh:**
```bash
python src/visualization/visualizer.py
```

**Input:** `data/metadata.csv`

**Output:** 4 biểu đồ PNG trong `reports/figures/`
- `category_distribution.png` - Phân bố category
- `size_histogram.png` - Histogram kích thước
- `scatter_width_height.png` - Scatter plot
- `statistics_summary.png` - Thống kê tổng hợp

**Thời gian:** ~30 giây

**Kết quả mong đợi:**
```
🚀 Data Visualization Pipeline
============================================================
📊 Đang đọc metadata...
✓ Đã đọc 199 images

🎨 Đang tạo visualizations...
✓ Đã lưu: reports\figures\category_distribution.png
✓ Đã lưu: reports\figures\size_histogram.png
✓ Đã lưu: reports\figures\scatter_width_height.png
✓ Đã lưu: reports\figures\statistics_summary.png

✅ Đã tạo xong! Kiểm tra thư mục: reports\figures
```

**Kiểm tra:**
```bash
# Mở thư mục biểu đồ
explorer reports\figures
```

---

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### BƯỚC 4: IMAGE PREPROCESSING (Xử lý ảnh)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Mục đích:** Resize ảnh, split train/val/test

**Lệnh:**
```bash
python src/image_processing/preprocessor.py
```

**Input:** 
- `data/metadata.csv`
- Ảnh trong `data/raw/`

**Output:** Ảnh đã xử lý trong `data/processed/`
- `data/processed/train/` - 126 ảnh (70%)
- `data/processed/val/` - 25 ảnh (14%)
- `data/processed/test/` - 29 ảnh (16%)

**Thời gian:** ~1-2 phút

**Kết quả mong đợi:**
```
🚀 Image Preprocessing Pipeline
============================================================
🚀 Bắt đầu preprocessing...
  Target size: (64, 64)
  Output dir: data\processed
  Total images: 199

📊 Chia dataset...

📋 Phân bố category:
  prohibitory    :  22 ảnh
  warning        :  10 ảnh
  mandatory      :  53 ảnh
  informative    : 114 ảnh

✓ Kết quả split:
  Train: 126 images (70.0%)
  Val:   25 images (13.9%)
  Test:  29 images (16.1%)

🔄 Đang xử lý train set...
Processing train: 100%|████████████| 126/126 [00:02<00:00, 50.12it/s]
✓ Đã xử lý 126/126 images cho train

🔄 Đang xử lý val set...
Processing val: 100%|██████████████| 25/25 [00:00<00:00, 52.31it/s]
✓ Đã xử lý 25/25 images cho val

🔄 Đang xử lý test set...
Processing test: 100%|█████████████| 29/29 [00:00<00:00, 51.78it/s]
✓ Đã xử lý 29/29 images cho test

============================================================
✅ Hoàn tất preprocessing!
============================================================
📁 Processed data: data\processed

📊 Tổng kết:
  - Train: 126 images
  - Val:   25 images
  - Test:  29 images
  - Total: 180 images
```

**Kiểm tra:**
```bash
# Đếm ảnh đã xử lý
Get-ChildItem -Path "data\processed" -Recurse -Filter *.png | Measure-Object | Select-Object -ExpandProperty Count
```

---

## 📝 SCRIPT CHẠY TẤT CẢ (All-in-one)

Nếu muốn chạy tất cả cùng lúc, tạo file `run_pipeline.ps1`:

```powershell
# run_pipeline.ps1
Write-Host "🚀 CHẠY TOÀN BỘ PIPELINE" -ForegroundColor Green
Write-Host "=" * 60

# Activate venv
.\venv\Scripts\Activate.ps1

# Bước 1: Scraping (bỏ qua nếu đã có data)
# Write-Host "`n📊 BƯỚC 1: Scraping..." -ForegroundColor Cyan
# python src/data_collection/scraper.py

# Bước 2: Cleaning
Write-Host "`n🧹 BƯỚC 2: Cleaning..." -ForegroundColor Cyan
python src/data_processing/cleaner.py

# Bước 3: Visualization
Write-Host "`n🎨 BƯỚC 3: Visualization..." -ForegroundColor Cyan
python src/visualization/visualizer.py

# Bước 4: Preprocessing
Write-Host "`n⚙️ BƯỚC 4: Preprocessing..." -ForegroundColor Cyan
python src/image_processing/preprocessor.py

Write-Host "`n✅ HOÀN TẤT TẤT CẢ!" -ForegroundColor Green
```

**Chạy:**
```bash
.\run_pipeline.ps1
```

---

## 🎯 TÓM TẮT NHANH

```bash
# Activate venv
.\venv\Scripts\Activate.ps1

# Chạy từng bước
python src/data_collection/scraper.py      # 1. Scraping
python src/data_processing/cleaner.py      # 2. Cleaning
python src/visualization/visualizer.py     # 3. Visualization
python src/image_processing/preprocessor.py # 4. Preprocessing
```

---

## ✅ CHECKLIST

- [ ] Bước 1: Scraping → `data/raw/` có 199 ảnh
- [ ] Bước 2: Cleaning → `data/metadata.csv` được tạo
- [ ] Bước 3: Visualization → `reports/figures/` có 4 biểu đồ
- [ ] Bước 4: Preprocessing → `data/processed/` có 180 ảnh

---

## 🐛 XỬ LÝ LỖI

### Lỗi: `imagehash not found`
```bash
pip install imagehash
```

### Lỗi: `No module named 'src'`
```bash
# Chạy từ thư mục gốc d:\1.KTDL\
cd d:\1.KTDL
```

### Lỗi: `Permission denied`
```bash
# Chạy PowerShell as Administrator
```

---

**Ngày:** 2026-01-06  
**Tổng thời gian:** ~5-10 phút (không tính scraping)
