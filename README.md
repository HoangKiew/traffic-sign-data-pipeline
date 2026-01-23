# Data Pipeline - Xử lý dữ liệu biển báo giao thông

Pipeline tự động thu thập, tiền xử lý, gán nhãn và chia tập dữ liệu hình ảnh biển báo giao thông.

## 📋 Mục tiêu

Tạo ra một tập dữ liệu sạch, đã được gán nhãn chính xác và chia tập (train/test) sẵn sàng cho việc training mô hình AI.

## 🏗️ Kiến trúc Pipeline

```
1. Thu thập dữ liệu (Data Collection)
   ├── MinIO: Lưu trữ ảnh thô
   └── MongoDB: Lưu trữ metadata

2. Tiền xử lý (Preprocessing)
   ├── Khử nhiễu (Bilateral/Median Filter)
   ├── Cân bằng sáng (CLAHE)
   ├── Tăng cường độ sắc nét (Unsharp Masking)
   └── Resize với padding

3. Xử lý và Gán nhãn (Processing & Labeling)
   ├── Detect: YOLO phát hiện biển báo
   ├── Crop: Cắt biển báo từ ảnh
   ├── Verify: VLM xác thực nhãn
   └── Filter: Lọc bỏ nhãn sai

4. Đóng gói (Finalizing)
   ├── Chia train/test (80/20)
   ├── Lưu ảnh và nhãn
   └── Thống kê dataset
```

## 📁 Cấu trúc thư mục

```
traffic-sign-data-pipeline/
├── config/
│   ├── config.py              # Cấu hình chính
│   └── .env.example           # Mẫu file cấu hình
├── data_collection/
│   └── collector.py           # Thu thập dữ liệu từ MinIO/MongoDB
├── preprocessing/
│   └── image_processor.py     # Tiền xử lý ảnh
├── processing_labeling/
│   ├── detector.py            # YOLO detection
│   ├── cropper.py             # Crop biển báo
│   ├── vlm_verifier.py        # VLM verification
│   └── labeler.py             # Quy trình gán nhãn
├── finalizing/
│   └── dataset_splitter.py    # Chia tập và thống kê
├── utils/
│   └── database.py            # MinIO và MongoDB clients
├── main.py                    # Script chính
├── sample_data.py             # Tạo dữ liệu mẫu
├── requirements.txt           # Dependencies
└── README.md                  # File này
```

## 🚀 Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình môi trường

Sao chép file `.env.example` và tạo file `.env`:

```bash
cp config/.env.example config/.env
```

Chỉnh sửa `config/.env` với thông tin của bạn:

```env
# MinIO Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=traffic_signs_db
```

### 3. Khởi động MinIO và MongoDB

**MinIO:**
```bash
# Docker
docker run -p 9000:9000 -p 9001:9001 \
  minio/minio server /data --console-address ":9001"
```

**MongoDB:**
```bash
# Docker
docker run -p 27017:27017 mongo
```

## 💻 Sử dụng

### Bước 1: Chuẩn bị dữ liệu

**Cách 1: Sử dụng dữ liệu mẫu (để test)**
```bash
python sample_data.py --num 10
```

**Cách 2: Upload dữ liệu thực tế**

- Upload ảnh biển báo lên MinIO bucket `traffic-signs-raw`
- Thêm metadata vào MongoDB collection `metadata` với format:
```json
{
  "image_name": "traffic_sign_001.jpg",
  "location": "Hanoi",
  "road_type": "highway",
  "weather": "sunny"
}
```

### Bước 2: Chạy Pipeline

```bash
python main.py
```

Pipeline sẽ tự động:
1. ✅ Thu thập ảnh từ MinIO và metadata từ MongoDB
2. ✅ Tiền xử lý ảnh (khử nhiễu, cân bằng sáng, tăng cường độ sắc nét)
3. ✅ Phát hiện biển báo bằng YOLO
4. ✅ Cắt và gán nhãn biển báo
5. ✅ Xác thực nhãn bằng VLM
6. ✅ Chia tập train/test (80/20)
7. ✅ Lưu kết quả và tạo thống kê

### Bước 3: Kiểm tra kết quả

Dataset được lưu tại thư mục `output/`:

```
output/
├── train/
│   ├── images/          # Ảnh train
│   └── labels/          # Nhãn train (.txt)
└── test/
    ├── images/          # Ảnh test
    └── labels/          # Nhãn test (.txt)
```

## ⚙️ Cấu hình nâng cao

Chỉnh sửa `config/config.py` để tùy chỉnh:

- **Kích thước ảnh:** `IMAGE_TARGET_SIZE = (640, 640)`
- **Tỷ lệ train/test:** `TRAIN_TEST_SPLIT_RATIO = 0.8`
- **Ngưỡng confidence YOLO:** `YOLO_CONFIDENCE_THRESHOLD = 0.5`
- **Model VLM:** `VLM_MODEL_NAME = "Salesforce/blip-image-captioning-base"`

## 📊 Thống kê

Pipeline tự động tạo thống kê về:
- Tổng số mẫu và số lớp
- Phân bố mẫu theo từng lớp
- Cảnh báo lớp có ít mẫu (< MIN_SAMPLES_PER_CLASS)

## 🔧 Xử lý sự cố

### Lỗi kết nối MinIO/MongoDB
- Kiểm tra service đã chạy chưa
- Kiểm tra thông tin kết nối trong `.env`

### Không phát hiện được biển báo
- YOLO mặc định chỉ detect "stop sign" (class_id=11)
- Cần fine-tune YOLO cho dataset biển báo cụ thể
- Hoặc chỉnh sửa `filter_traffic_signs()` trong `detector.py`

### VLM verification không hoạt động
- Model VLM sẽ tự động tải từ HuggingFace
- Nếu không có internet, pipeline sẽ bỏ qua verification
- Có thể chỉnh `VLM_DEVICE = "cuda"` nếu có GPU

## 📝 Lưu ý

1. **YOLO Model:** Mặc định sử dụng YOLOv8n (nano). Có thể thay bằng model lớn hơn hoặc model đã fine-tune cho biển báo.

2. **VLM Verification:** BLIP model có thể không chính xác 100%. Có thể thay bằng model khác hoặc bỏ qua bước này.

3. **Metadata:** Đảm bảo metadata trong MongoDB có trường `image_name` khớp với tên file trong MinIO.

## 📄 License

MIT License

## 👥 Tác giả

Data Mining Project - Năm 3 Kỳ 1
