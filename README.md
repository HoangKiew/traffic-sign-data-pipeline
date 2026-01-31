# Traffic Sign Detection & Classification Pipeline

Hệ thống thu thập, xử lý và phân loại biển báo giao thông tự động sử dụng YOLO và Computer Vision.

## 📋 Tính năng

- ✅ **Web Scraping**: Thu thập tự động 5000+ ảnh từ Google/Bing
- ✅ **Preprocessing**: Khử nhiễu, cân bằng sáng, tăng nét
- ✅ **Object Detection**: YOLO batch processing (10-20x faster)
- ✅ **Classification**: Phân loại 5 classes dựa trên màu sắc
- ✅ **Storage**: MinIO (ảnh) + MongoDB (metadata)
- ✅ **Visualization**: 10 biểu đồ phân tích chi tiết

## 🎯 Kết quả

- **Dataset**: 9,754 biển báo từ 3,220 ảnh
- **Classes**: Cấm, Nguy hiểm, Hiệu lệnh, Chỉ dẫn, Khác
- **Format**: YOLO labels (.txt)
- **Success rate**: 56.3% (ảnh có biển báo)

---

## 🚀 Cài đặt

### 1. Clone repository

```bash
git clone https://github.com/HoangKiew/traffic-sign-data-pipeline.git
cd traffic-sign-data-pipeline
```

### 2. Tạo virtual environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Cài đặt dependencies (BẮT BUỘC: Cài thư viện Python, bao gồm minio)

```bash
pip install -r requirements.txt
```

### 4. Khởi động MinIO và MongoDB (Docker)

```bash
docker-compose up -d
```

Kiểm tra services:
```bash
docker ps
```

### 5. Download YOLO model (tự động khi chạy lần đầu)

Model YOLOv8n sẽ tự động download khi chạy script lần đầu.

---

## 📖 Cách sử dụng

### Option 1: Chạy toàn bộ pipeline (Tự động)

```bash
python unified_pipeline.py
```

### Option 2: Chạy từng bước (Thủ công)

#### Bước 1: Thu thập dữ liệu
```bash
python download_from_web.py
```
- Thu thập ~5000 ảnh từ Internet
- Upload lên MinIO bucket `traffic-signs-raw`
- Thời gian: ~30-60 phút

#### Bước 2: Lọc nhanh (Optional)
```bash
python fast_filter.py
```
- Loại bỏ ảnh rác, trùng lặp
- Thời gian: ~2-5 phút

#### Bước 3: Tiền xử lý
```bash
python main.py
```
- Khử nhiễu, cân bằng sáng, tăng nét
- Lọc ảnh không có biển báo
- Upload lên MinIO bucket `traffic-signs-processed`
- Thời gian: ~15-30 phút

#### Bước 4: Detection & Classification
```bash
python fast_detection.py
```
- YOLO detection + Color classification
- Tạo labels YOLO format
- Lưu tại `datasets/labels/`
- Thời gian: ~8-15 phút

#### Bước 5: Visualization
```bash
python visualize_analytics.py
```
- Tạo 10 biểu đồ phân tích
- Lưu tại `analytics_charts/`
- Thời gian: ~1-2 phút

#### Bước 6: Upload MongoDB (Optional)
```bash
python label_data.py
```
- Lưu metadata vào MongoDB
- Thời gian: ~2-5 phút

---

## 📁 Cấu trúc thư mục

```
traffic-sign-data-pipeline/
├── config/                    # Cấu hình
│   ├── config.py
│   ├── optimization_config.py
│   └── web_sources_config.py
├── data_collection/           # Web scraping
│   └── web_scraper.py
├── preprocessing/             # Tiền xử lý ảnh
│   └── image_processor.py
├── processing_labeling/       # Detection & labeling
│   ├── detector.py
│   └── labeler.py
├── utils/                     # Utilities
│   ├── database.py           # MinIO + MongoDB
│   ├── logger.py
│   └── performance_monitor.py
├── download_from_web.py       # Script 1: Crawl
├── fast_filter.py             # Script 2: Filter
├── main.py                    # Script 3: Preprocess
├── fast_detection.py          # Script 4: Detect
├── label_data.py              # Script 5: Label
├── visualize_analytics.py     # Script 6: Visualize
├── unified_pipeline.py        # Chạy tất cả
├── requirements.txt           # Dependencies
└── README.md                  # Tài liệu này
```

---

## 🔧 Cấu hình

### MinIO (Object Storage)
- **URL**: http://localhost:9000
- **Console**: http://localhost:9001
- **Username**: minioadmin
- **Password**: minioadmin

### MongoDB (Document Database)
- **URL**: mongodb://localhost:27017
- **Database**: traffic_signs_db
- **Collection**: dataset_labels_v1

### YOLO
- **Model**: YOLOv8n (nano)
- **Confidence**: 0.25
- **Batch size**: 16

---

## 📊 Xem kết quả

### 1. Xem ảnh trên MinIO Console
```
http://localhost:9001
```
- Bucket `traffic-signs-raw`: Ảnh gốc
- Bucket `traffic-signs-processed`: Ảnh đã xử lý

### 2. Xem biểu đồ phân tích
```bash
# Mở thư mục
cd analytics_charts
```

### 3. Xem metadata trên MongoDB
```bash
docker exec -it mongo_server mongosh

use traffic_signs_db
db.dataset_labels_v1.countDocuments()
db.dataset_labels_v1.findOne()
```

### 4. Download ảnh về local
```bash
python view_images.py --view 10 --download
```

---

## 🎨 Biểu đồ phân tích

Script `visualize_analytics.py` tạo 10 biểu đồ:

1. **class_count.png** - Số lượng theo loại
2. **class_percentage.png** - Tỷ lệ % theo loại
3. **size_distribution.png** - Phân bố kích thước
4. **area_by_class.png** - Diện tích theo loại
5. **width_vs_height.png** - Chiều rộng vs cao
6. **aspect_ratio.png** - Tỷ lệ khung hình
7. **location_heatmap.png** - Bản đồ nhiệt vị trí
8. **location_by_class.png** - Vị trí theo loại
9. **area_histogram.png** - Histogram diện tích
10. **summary_statistics.png** - Bảng thống kê

---

## ⚙️ Tối ưu hóa

### Batch Processing
- YOLO: 16 ảnh/batch → **10-20x nhanh hơn**
- MinIO upload: 100 ảnh/batch
- MongoDB insert: Bulk operations

### Error Recovery
- Retry với exponential backoff (3 lần)
- Skip on error (tiếp tục khi gặp lỗi)
- Graceful shutdown (Ctrl+C lưu checkpoint)

### Memory Management
- Streaming thay vì load all
- Giới hạn 1000 ảnh in-memory
- Cleanup sau mỗi batch

---

## 🐛 Troubleshooting

### Lỗi: MinIO connection refused
```bash
docker-compose restart minio
```

### Lỗi: MongoDB connection timeout
```bash
docker-compose restart mongo
```

### Lỗi: YOLO model not found
Model sẽ tự động download. Nếu lỗi, download thủ công:
```bash
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

### Lỗi: Out of memory
Giảm batch size trong `config/optimization_config.py`:
```python
YOLO_BATCH_SIZE = 8  # Giảm từ 16 xuống 8
```

---

## 📚 Tài liệu

- [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) - Hướng dẫn tối ưu hóa
- [GIT_GUIDE.md](GIT_GUIDE.md) - Hướng dẫn Git
- [PRESENTATION.md](PRESENTATION.md) - Bài thuyết trình

---

## 🤝 Đóng góp

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📝 License

MIT License

---

## 👤 Tác giả

**HoangKiew**
- GitHub: [@HoangKiew](https://github.com/HoangKiew)
- Repository: [traffic-sign-data-pipeline](https://github.com/HoangKiew/traffic-sign-data-pipeline)

---

## 🙏 Cảm ơn

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [MinIO](https://min.io/)
- [MongoDB](https://www.mongodb.com/)
- [OpenCV](https://opencv.org/)

---

## 📊 Thống kê Project

- **Lines of Code**: ~4,500
- **Files**: 39
- **Dataset Size**: 9,754 objects
- **Success Rate**: 56.3%
- **Processing Time**: ~1-2 giờ cho 5000 ảnh

## 🧪 So sánh kết quả nhận diện giữa 2 mô hình YOLO

Pipeline hỗ trợ chạy song song 2 mô hình YOLO (YOLOv8n và YOLOv8x) để đánh giá chất lượng nhận diện biển báo giao thông.

- **YOLOv8n**: Model nhẹ, tốc độ nhanh, phù hợp cho thiết bị hạn chế tài nguyên.
- **YOLOv8x**: Model lớn, chính xác cao hơn, phù hợp cho đánh giá chất lượng.

### Cách chạy so sánh:

```bash
python master_pipeline.py --compare
```

- Ảnh kết quả sẽ được lưu tại thư mục `compare_results/`
- Khung **xanh lá**: Kết quả nhận diện của YOLOv8n
- Khung **đỏ**: Kết quả nhận diện của YOLOv8x
- Có thể so sánh số lượng, vị trí, loại biển báo giữa hai mô hình.

### Ý nghĩa:

- Giúp đánh giá mô hình nào phù hợp hơn cho bài toán nhận diện biển báo giao thông thực tế.
- Phát hiện các trường hợp mô hình nhận diện khác nhau (trùng, thiếu, thừa).
- Hỗ trợ kiểm tra chất lượng dữ liệu và pipeline.
