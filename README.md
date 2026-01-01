# Traffic Sign Data Pipeline - Quick Start Guide

## 🎯 Mục tiêu Đề tài
Xây dựng Data Pipeline hoàn chỉnh để thu thập, xử lý và phân loại hình ảnh biển báo giao thông.

## 📋 Các bước thực hiện

### Bước 1: Setup môi trường
```bash
# Tạo virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Cài đặt dependencies
pip install -r requirements.txt
```

### Bước 2: Thu thập dữ liệu (Web Scraping)
```bash
# Xem hướng dẫn chi tiết
cat SCRAPING_GUIDE.md

# Cách 1: Scrape tự động (khuyên dùng)
python auto_scrape.py

# Cách 2: Scrape thủ công
python src/data_collection/scraper.py
python src/data_collection/selenium_scraper.py
```

### Bước 3: Xử lý và trực quan hóa
```bash
# Clean data
python src/data_processing/cleaner.py

# Tạo visualizations
python src/visualization/visualizer.py
```

### Bước 4: Training model
```bash
# Preprocess images
python src/image_processing/preprocessor.py

# Train model
python src/models/trainer.py --model cnn --epochs 50
```

### Bước 5: Đánh giá
```bash
# Evaluate model
python src/evaluation/evaluator.py

# Generate report
python src/evaluation/generate_report.py
```

## 📊 Workflow Pipeline

```
Raw Data → Collection → Cleaning → DataFrame → Visualization
                                              ↓
                                    Image Processing
                                              ↓
                                      Model Training
                                              ↓
                                    Classification & Report
```

## 🛠️ Tech Stack
- **Data**: pandas, numpy
- **Visualization**: matplotlib, seaborn, plotly
- **ML**: TensorFlow/Keras hoặc PyTorch
- **Image**: OpenCV, Pillow

## 📁 Cấu trúc thư mục
```
traffic-sign-pipeline/
├── data/raw/          # Raw images
├── data/processed/    # Processed images
├── src/               # Source code
├── notebooks/         # Jupyter notebooks
├── reports/           # Reports & figures
└── models/            # Saved models
```

## 📚 Tài liệu chi tiết
Xem [implementation_plan.md](file:///C:/Users/ASUS/.gemini/antigravity/brain/5e517c3e-38f5-4c3c-9a63-bc893c1da920/implementation_plan.md) để biết chi tiết kỹ thuật.

## ✅ Checklist
Xem [task.md](file:///C:/Users/ASUS/.gemini/antigravity/brain/5e517c3e-38f5-4c3c-9a63-bc893c1da920/task.md) để theo dõi tiến độ.
