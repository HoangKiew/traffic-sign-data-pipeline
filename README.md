# Traffic Sign Data Pipeline using MongoDB

## 1. Giới thiệu

Dự án này xây dựng **Data Pipeline thu thập và xử lý dữ liệu hình ảnh biển báo giao thông**, phục vụ cho bài toán **phân loại (classification)**. Pipeline được thiết kế theo đúng tư duy **Data Mining**, trong đó:

* **MongoDB** đóng vai trò trung tâm lưu trữ metadata và trạng thái xử lý dữ liệu.
* **Ảnh được lưu trên file system**, không lưu trực tiếp trong database.
* **Mô hình học máy chỉ đóng vai trò hỗ trợ kiểm tra và đánh giá dữ liệu**, không phải trọng tâm chính.

Pipeline đảm bảo khả năng mở rộng, lặp lại (feedback loop) và có sự tham gia của con người (human-in-the-loop).

---

## 2. Mục tiêu

* Thu thập dữ liệu hình ảnh biển báo giao thông từ nhiều nguồn
* Chuẩn hóa và làm sạch dữ liệu ảnh
* Quản lý metadata và trạng thái dữ liệu bằng MongoDB
* Tạo tập dữ liệu đáng tin cậy cho bài toán phân loại biển báo giao thông
* Đánh giá chất lượng **dataset**, không chỉ đánh giá mô hình

---

## 3. Kiến trúc tổng thể Data Pipeline

```
Raw Images
   ↓
Preprocess
   ↓
Transform
   ↓
Auto Label (YOLO)
   ↓
Human Verify
   ↓
Split Dataset
   ↓
Evaluate Dataset
```

**MongoDB** lưu toàn bộ metadata, annotation và trạng thái pipeline ở từng bước.

---

## 4. Cấu trúc thư mục

```
traffic_sign_pipeline/
│
├── data/
│   ├── raw_images/              # Ảnh thô ban đầu
│   ├── processed_images/        # Ảnh sau tiền xử lý
│   ├── transformed_images/      # Ảnh resize + padding
│   └── labeled_images/          # (tuỳ chọn) xuất dataset
│
├── models/
│   └── yolov8n.pt               # Model pretrained dùng để auto label
│
├── src/
│   ├── config.py                # Cấu hình chung
│   ├── db.py                    # Kết nối MongoDB
│   ├── collect_data.py          # Thu thập metadata ảnh
│   ├── preprocess.py            # Tiền xử lý ảnh
│   ├── transform.py             # Chuẩn hóa kích thước ảnh
│   ├── auto_label.py            # Gán nhãn tự động bằng YOLO
│   ├── human_verify.py          # Xác nhận nhãn (human-in-the-loop)
│   ├── split_dataset.py         # Chia train / val / test
│   └── evaluate_dataset.py      # Đánh giá dataset
│
├── requirements.txt
└── README.md
```

---

## 5. Thiết kế MongoDB

### 5.1 Database

```
traffic_sign_db
```

### 5.2 Collections

#### images

Lưu metadata và trạng thái xử lý của ảnh

* filename
* raw_path
* processed_path
* transformed_path
* stage (raw / processed / transformed)

#### annotations

Lưu nhãn do mô hình và con người xác nhận

* image_id
* label
* confidence
* verified
* model

#### splits

Quản lý việc chia tập dữ liệu

* image_id
* dataset_split (train / val / test)

---

## 6. Quy trình chạy pipeline

### Bước 1: Cài đặt thư viện

```
pip install -r requirements.txt
```

### Bước 2: Chuẩn bị dữ liệu

* Đặt ảnh biển báo giao thông vào thư mục `data/raw_images/`
* Khởi động MongoDB local

### Bước 3: Chạy pipeline theo thứ tự

```
python src/collect_data.py
python src/preprocess.py
python src/transform.py
python src/auto_label.py
python src/human_verify.py
python src/split_dataset.py
python src/evaluate_dataset.py
```

---

## 7. Đánh giá

Dự án tập trung vào **đánh giá chất lượng dữ liệu** thông qua:

* Tỷ lệ nhãn được xác nhận (verified)
* Phân bố dữ liệu train / val / test
* Khả năng phát hiện nhãn sai thông qua mô hình

Pipeline có thể mở rộng bằng cách:

* Thêm mô hình khác để cross-check
* Bổ sung bước fine-tuning
* Tăng dữ liệu và lặp lại pipeline

---

## 8. Kết luận

* Data Pipeline là một **vòng lặp liên tục** giữa dữ liệu – mô hình – con người
* Chất lượng dữ liệu quyết định phần lớn hiệu quả mô hình
* MongoDB giúp quản lý metadata và trạng thái pipeline một cách linh hoạt

Dự án đáp ứng đầy đủ yêu cầu học phần **Data Mining / Machine Learning ứng dụng**.

---

## 9. Ghi chú thuyết trình

> *"Model chỉ là công cụ hỗ trợ, dữ liệu mới là yếu tố quyết định."*

Pipeline này được xây dựng đúng theo tư duy thực tế trong các hệ thống AI/Data thực tế.
