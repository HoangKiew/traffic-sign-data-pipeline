# Traffic Sign Data Pipeline

## 🎯 Mục tiêu
Pipeline đơn giản để thu thập, làm sạch và trực quan hóa dữ liệu biển báo giao thông.

## 📋 3 Bước Chính

### 1️⃣ Web Scraping - Thu thập dữ liệu từ trình duyệt
### 2️⃣ Data Cleaning - Làm sạch dữ liệu
### 3️⃣ Visualization - Trực quan hóa bằng biểu đồ

---

## 🚀 Quick Start

### Cài đặt
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Chạy Pipeline
```bash
python main.py
```

**Kết quả:**
- ✅ `data/raw/` - Ảnh gốc đã scrape
- ✅ `data/metadata.csv` - Metadata đã clean
- ✅ `reports/figures/` - Nhiều biểu đồ visualization (cơ bản + nâng cao)

---

## 📊 Workflow

```
Web Scraping → Data Cleaning → Visualization
     ↓              ↓              ↓
  data/raw/    metadata.csv   reports/figures/
```

---

## 📁 Cấu trúc

```
traffic-sign-data-pipeline/
├── data/
│   ├── raw/              # Ảnh gốc đã scrape
│   └── metadata.csv      # Metadata đã clean
├── reports/
│   └── figures/          # 4 biểu đồ
└── src/
    ├── data_collection/  # Scraper
    ├── data_processing/  # Cleaner
    └── visualization/    # Visualizer
```

---

## 📚 Tài liệu

- **📖 Hướng dẫn chạy chi tiết:** [`CACH_CHAY.md`](CACH_CHAY.md) ⭐
- **📊 Giải thích biểu đồ:** [`GIAI_THICH_BIEU_DO.md`](GIAI_THICH_BIEU_DO.md) ⭐
- **📋 Hướng dẫn đầy đủ:** [`HUONG_DAN_DON_GIAN.md`](HUONG_DAN_DON_GIAN.md)
- **Quick start:** Chạy `python main.py`

---

## 🛠️ Tech Stack

- **Scraping:** requests, beautifulsoup4
- **Data:** pandas, numpy
- **Visualization:** matplotlib, seaborn
- **Image:** Pillow
