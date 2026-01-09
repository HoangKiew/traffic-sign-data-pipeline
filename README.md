```markdown
# Traffic Sign Data Pipeline - Quick Start Guide

## Mục tiêu
Thu thập → xử lý → trực quan hóa hình ảnh biển báo giao thông (4 loại: prohibitory, warning, mandatory, informative).

## Các bước thực hiện

### 1. Setup môi trường
```bash
# Tạo venv (Windows)
python -m venv venv
venv\Scripts\activate

# Cài dependencies
pip install -r requirements.txt
```

### 2. Thu thập dữ liệu (Scraping)
```bash
# Chạy scraper chính (BeautifulSoup + requests)
python src/data_collection/scraper.py
```
→ Ảnh lưu vào: `data/raw/`

### 3. Xử lý & trực quan hóa
```bash
# Clean + split + resize ảnh
python src/data_processing/cleaner.py

# Tạo báo cáo & biểu đồ
python src/visualization/visualizer.py
```
→ Kết quả:
- Metadata: `data/metadata.csv`
- Ảnh resize: `data/processed/train|val|test/...`
- Biểu đồ: `reports/figures/`

### 4. Kiểm tra nhanh
```bash
# Xem số lượng ảnh theo category
python -c "import pandas as pd; print(pd.read_csv('data/metadata.csv')['category'].value_counts())"
```

## Kết quả mong đợi (từ log)
- Tổng ảnh sau clean: ~1433
- Train/Val/Test: 1000 / 215 / 218
- Biểu đồ: Phân bố category, histogram size, scatter width-height, boxplot, file size

## Tech Stack
- Data: pandas, numpy
- Image: Pillow, tqdm
- Viz: matplotlib, seaborn

## Cấu trúc thư mục chính
```
traffic-sign-pipeline/
├── data/
│   ├── raw/           # Ảnh gốc từ scraper
│   ├── processed/     # Ảnh resize (train/val/test)
│   └── metadata.csv
├── src/
│   ├── data_collection/   # scraper.py
│   ├── data_processing/   # cleaner.py
│   └── visualization/     # visualizer.py
├── reports/figures/
└── requirements.txt
└── main.py
```

