# Traffic Sign Detection & Classification Pipeline

Hệ thống tự động thu thập, xử lý, nhận diện và phân loại biển báo giao thông sử dụng YOLO và Computer Vision.

## 🚦 Pipeline tổng quan

> **Khuyến nghị:**  
> **NÊN sử dụng script `unified_pipeline.py` để chạy toàn bộ pipeline tự động, bao gồm cả việc tự tạo bucket MinIO nếu chưa có.**  
> Các bước bên dưới có thể chạy riêng lẻ, nhưng chạy unified_pipeline sẽ đảm bảo mọi cấu hình và khởi tạo đều đúng thứ tự.

1. **Khởi động MinIO & MongoDB**
   ```bash
   docker-compose up -d
   ```

2. **Thu thập ảnh từ Internet**
   ```bash
   python scripts/download_from_web.py
   ```

3. **Lọc nhanh ảnh lỗi, trùng**
   ```bash
   python scripts/fast_filter.py
   ```

4. **Tiền xử lý & Detect biển báo**
   ```bash
   python scripts/main.py
   ```

5. **Phân loại màu sắc & Sinh nhãn YOLO**
   - **Nên chọn:**  
     - **Single YOLO:** Nếu chỉ muốn dùng 1 model YOLOv8n (nhanh, nhẹ, phù hợp đa số trường hợp).
     - **Dual YOLO:** Nếu muốn so sánh kết quả giữa YOLOv8n và YOLOv8x (chính xác hơn, nhưng chậm hơn).
   - **Lệnh chạy:**
     - Single YOLO:
       ```bash
       python processing_labeling/master_pipeline.py
       ```
     - Dual YOLO:
       ```bash
       python processing_labeling/master_pipeline.py --dual-yolo
       ```

6. **Gán nhãn, lưu metadata lên MongoDB**
   - **Nên chọn:**  
     - **Dual YOLO:** Nếu đã chạy bước trên với `--dual-yolo` để lưu cả hai kết quả vào database.
     - **Single YOLO:** Nếu chỉ dùng YOLOv8n, thêm `--single-yolo` để chỉ lưu nhãn từ model này.
   - **Lệnh chạy:**
     - Dual YOLO (khuyến nghị nếu đã dùng dual ở bước 5):
       ```bash
       python scripts/label_data.py
       ```
     - Single YOLO:
       ```bash
       python scripts/label_data.py --single-yolo
       ```

7. **Phân tích, visualize dữ liệu**
   ```bash
   python scripts/visualize_analytics.py
   ```
   > **Lưu ý:** Nếu gặp lỗi "Không tìm thấy file labels trong datasets/labels" hoặc "Không có dữ liệu để visualize!", hãy chắc chắn bạn đã chạy bước phân loại & sinh nhãn YOLO trước đó:
   > ```bash
   > python processing_labeling/master_pipeline.py
   > ```
   > hoặc kiểm tra lại đường dẫn thư mục labels.
   > **Mặc định, nhãn sẽ được lưu ở `datasets/labels_n/` (YOLOv8n) hoặc `datasets/labels_x/` (YOLOv8x).**
   > Nếu script visualize mặc định tìm ở `datasets/labels/`, hãy đổi lại tham số hoặc copy nhãn sang đúng thư mục.

8. **Tách train/val/test (nếu cần)**
   ```bash
   python scripts/data_split.py
   ```

9. **Chuẩn bị dữ liệu crop cho classification**
   - **Bạn có thể chọn:**
     - **Cách 1 (khuyến nghị):** Không cần tải về, train trực tiếp trên dữ liệu crop đã lưu trên MinIO.
     - **Cách 2:** Nếu muốn train local, dùng script để tải crop về máy:
       ```bash
       python scripts/download_crops_by_class.py
       ```

10. **Huấn luyện model phân loại**
    - **Nếu train trực tiếp trên MinIO:**  
      Chỉ cần chạy:
      ```bash
      python scripts/train_classification.py
      ```
      Script này đã hỗ trợ đọc dữ liệu trực tiếp từ MinIO, không cần tải về local.
      Đảm bảo bạn đã cấu hình đúng thông tin MinIO và bucket trong file `train_classification.py`.
    - **Nếu đã tải crop về local:**  
      ```bash
      python scripts/train_classification.py
      ```

11. **Kiểm tra kết quả với UI**
    ```bash
    streamlit run scripts/ui_predict.py
    ```

---

## 📁 Cấu trúc thư mục

```
traffic-sign-data-pipeline/
├── config/
├── data_collection/
├── preprocessing/
├── processing_labeling/
├── utils/
├── outputs/
├── datasets/
├── scripts/
├── docker-compose.yml
├── requirements.txt
├── README.md
└── ...
```

---

## 🔧 Cấu hình dịch vụ

- **MinIO:** http://localhost:9000 (console: :9001, user/pass: minioadmin)
- **MongoDB:** mongodb://localhost:27017, db: traffic_signs_db, collection: dataset_labels_v1
- **YOLO:** Model YOLOv8n (hoặc YOLOv8x nếu dual), batch size 16

---

## 📝 License & Tác giả

MIT License  
**HoangKiew** - [GitHub](https://github.com/HoangKiew)

---

## 💡 Ghi chú

- **NÊN chạy tự động toàn bộ pipeline bằng:**
  ```bash
  python scripts/unified_pipeline.py
  ```
  - Script này sẽ tự động gọi hàm tạo bucket MinIO nếu chưa có (xem `config/config.py`).
  - Đảm bảo mọi bước đều đúng thứ tự, tránh lỗi thiếu bucket hoặc thư mục.
- Nếu dùng dual YOLO, cần sửa đường dẫn đầu ra cho các bước phân tích/visualize.
- Dữ liệu crop cho classification được phân loại tự động, không cần thao tác tay.
- Có thể train classification trực tiếp trên dữ liệu crop lưu trên MinIO mà không cần tải về local, nếu script hỗ trợ.

---

## 📦 OUTPUT CUỐI CÙNG SAU KHI TRAIN/GÁN NHÃN

- **Nhãn YOLOv8n:** `datasets/labels_n/`
- **Nhãn YOLOv8x:** `datasets/labels_x/`
- **Metadata MongoDB:** Collection `dataset_labels_v1`
- **Biểu đồ so sánh:** `compare_results/` (overall_compare.png, class_compare.png, difference_chart.png)

> **Lưu ý:**  
> Nếu bạn dùng script phân tích/visualize mà mặc định đọc từ `datasets/labels/`, hãy chỉ định lại đường dẫn đúng (`datasets/labels_n/` hoặc `datasets/labels_x/`) hoặc copy nhãn sang thư mục đó.
