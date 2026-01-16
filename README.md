# Traffic Sign Data Pipeline – Quick Start Guide (Data-Only)

## Mục tiêu

Xây dựng **Data Pipeline** thu thập và xử lý **dữ liệu hình ảnh biển báo giao thông công khai**
(4 loại: `prohibitory`, `warning`, `mandatory`, `informative`) nhằm:

* Thu thập dữ liệu ảnh
* Làm sạch & chuẩn hóa
* Tạo metadata
* Lưu trữ vào **MongoDB**
* Trực quan hóa & phân tích dữ liệu (EDA)

---

## 1. Setup môi trường

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2. Thu thập dữ liệu (Scraping)

```bash
python src/data_collection/scraper.py
```

Ảnh được lưu tại:

```
data/raw/<category>/*.jpg|png
```

---

## 3. Chạy toàn bộ Data Pipeline

```bash
python main.py
```

Pipeline thực hiện:

### 1️⃣ Web Scraping (tuỳ chọn)

* Kiểm tra `data/raw/` đã có ảnh hay chưa
* Nếu đã có → hỏi có scrape thêm không
* Nếu chưa có → hướng dẫn chạy scraper

---

### 2️⃣ Data Cleaning & Preprocessing

* Tạo metadata:

  * width, height, size, format
  * category
  * đường dẫn ảnh
* Tính **MD5 hash** → phát hiện ảnh trùng chính xác
* Tính **perceptual hash (pHash)** → phát hiện ảnh gần giống
* Phân tích EDA cơ bản
* Kiểm tra missing values & outliers
* **Detect và loại bỏ ảnh mờ** (Laplacian variance)
* Làm sạch dữ liệu

---

### 3️⃣ Data Integration → MongoDB

* Đẩy metadata (và tuỳ chọn bytes ảnh) lên MongoDB:

  * Database: `traffic_signs_db`
  * Collection: `images`

---

### 4️⃣ Split & Resize Dataset

* Chia **train / val / test** theo từng category
  (xử lý trường hợp ít ảnh)
* Resize ảnh về **224×224**
* Lưu tại:

```
data/processed/
├── train/
├── val/
└── test/
```

---

### 5️⃣ Visualization (EDA)

* Đọc metadata từ:

  * MongoDB (`traffic_signs_db.images`)
* Vẽ các biểu đồ:

  * Phân bố số ảnh theo category
  * Histogram width / height
  * Scatter width vs height
  * Thống kê kích thước ảnh
* Lưu tại:

```
reports/figures/
```

---

## 4. Chạy từng bước riêng lẻ (tuỳ chọn)

### 4.1 Scraping độc lập

```bash
python src/data_collection/scraper.py
```

---

### 4.2 Cleaning + MongoDB độc lập

```bash
python src/data_processing/cleaner.py
```

---

### 4.3 Visualization độc lập

```bash
python src/visualization/visualizer.py
```

---

## 5. Kết quả

* Ảnh gốc: `data/raw/`
* Ảnh đã xử lý: `data/processed/`
* Metadata: MongoDB `traffic_signs_db.images`
* Biểu đồ EDA: `reports/figures/`

---

## 6. Tech Stack

* **Web scraping**: `requests`, `BeautifulSoup`, `Selenium`
* **Data processing**: `pandas`, `numpy`, `tqdm`
* **Image processing**: `Pillow`, `opencv-python`, `imagehash`
* **Storage**: MongoDB Atlas (`pymongo`)
* **Visualization**: `matplotlib`, `seaborn`, `plotly`

---

## 7. Cấu trúc thư mục

```text
traffic-sign-data-pipeline/
├── data/
│   ├── raw/                 # Ảnh gốc
│   └── processed/           # Ảnh đã split + resize
├── src/
│   ├── data_collection/     # scraper.py
│   ├── data_processing/     # cleaner.py
│   └── visualization/       # visualizer.py
├── reports/
│   └── figures/             # Biểu đồ EDA
├── cleanup_results.py       # Script dọn kết quả + MongoDB
├── main.py                  # Orchestrator (data-only)
└── requirements.txt
```

---

## 8. Cleanup kết quả

```bash
python cleanup_results.py
```

Script sẽ (có hỏi xác nhận):

* Xóa `data/processed/`
* Xóa `reports/`
* Tuỳ chọn xóa toàn bộ dữ liệu trong MongoDB
  `traffic_signs_db.images`

---



